#!/usr/bin/env python3
"""
ScanX Stock Data Getter Controller
=================================
DB-first reader with on-demand scrape for missing symbols/fields.

Features:
- Queries MongoDB collection 'scanx_stocks_data' by symbol
- If data is missing/stale, triggers ScanXStockDataController.scrape_single_symbol
- Per-symbol in-process concurrency lock to avoid duplicate scrapes
- Small helpers to return specific sections efficiently

Notes:
- Locks are process-local. If you run multiple workers, consider a DB-based lock or queue.
- Uses project-standard logger and response utils.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta

from Utils.logger import get_logger
from Utils.db import DatabaseManager

# Reuse the scraping controller for on-demand fills
from API.Controller.scanx_scrap_stocks_data_by_symbol import ScanXStockDataController

logger = get_logger(__name__)


class ScanXStockDataGetterController:
    """
    Reads ScanX stock data from MongoDB with DB-first strategy.
    If a required field is missing for a symbol, performs a one-time scrape and returns the updated doc.
    """

    # In-process locks per symbol to avoid duplicate concurrent scrapes
    _locks: Dict[str, threading.Lock] = {}
    _events: Dict[str, threading.Event] = {}

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.collection_name = "scanx_stocks_data"
        self.scraper = ScanXStockDataController()

    # -------------- DB helpers --------------
    def _get_doc(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            return self.db_manager.mongo_db[self.collection_name].find_one({"symbol": symbol.upper()})
        except Exception as e:
            logger.error(f"DB read failed for {symbol}: {e}")
            return None

    def _has_required_fields(self, doc: Optional[Dict[str, Any]], fields: List[str]) -> bool:
        if not doc:
            return False
        for f in fields:
            val = doc.get(f)
            if val is None:
                return False
            # Allow empty list/dict for some fields but treat None as missing
        return True

    # -------------- Concurrency helpers --------------
    @classmethod
    def _get_lock(cls, symbol: str) -> threading.Lock:
        key = symbol.upper()
        if key not in cls._locks:
            cls._locks[key] = threading.Lock()
        return cls._locks[key]

    @classmethod
    def _get_event(cls, symbol: str) -> threading.Event:
        key = symbol.upper()
        if key not in cls._events:
            cls._events[key] = threading.Event()
        return cls._events[key]

    def _ensure_data(self, symbol: str, required_fields: List[str], wait_timeout: float = 300.0) -> Optional[Dict[str, Any]]:
        """
        Ensure the document for symbol has the required fields.
        - If present, return immediately.
        - If missing, acquire a per-symbol lock and run a scrape once.
        - If another thread is scraping, wait for completion (up to wait_timeout) and then return from DB.
        """
        # Fast path
        doc = self._get_doc(symbol)
        if self._has_required_fields(doc, required_fields):
            return doc

        lock = self._get_lock(symbol)
        event = self._get_event(symbol)

        # Try to be the scraper
        acquired = lock.acquire(blocking=False)
        if acquired:
            try:
                # Reset event before scrape so waiters can wait
                try:
                    event.clear()
                except Exception:
                    pass

                logger.info(f"Triggering scrape for missing data: symbol={symbol}, fields={required_fields}")
                self.scraper.scrape_single_symbol(symbol.upper())
            except Exception as e:
                logger.error(f"Scrape failed for {symbol}: {e}")
            finally:
                # Signal completion to waiters regardless of success
                try:
                    event.set()
                except Exception:
                    pass
                lock.release()

            # Read again after scrape
            return self._get_doc(symbol)
        else:
            # Someone else is scraping. Wait until they signal.
            logger.info(f"Waiting for in-flight scrape to finish: symbol={symbol}")
            try:
                event.wait(timeout=wait_timeout)
            except Exception:
                pass
            return self._get_doc(symbol)

    # -------------- Public getters --------------
    def get_section(self, symbol: str, field: str, ensure: bool = True) -> Optional[Any]:
        required = [field]
        doc = self._ensure_data(symbol, required) if ensure else self._get_doc(symbol)
        if not doc:
            return None
        return doc.get(field)

    def get_sections(self, symbol: str, fields: List[str], ensure: bool = True) -> Optional[Dict[str, Any]]:
        doc = self._ensure_data(symbol, fields) if ensure else self._get_doc(symbol)
        if not doc:
            return None
        return {f: doc.get(f) for f in fields}

    def get_financials_bundle(self, symbol: str) -> Optional[Dict[str, Any]]:
        fields = [
            "balance_sheet_consolidated",
            "balance_sheet_standalone",
            "cash_flow_consolidated",
            "cash_flow_standalone",
            "financial_results_quarterly_consolidated",
            "financial_results_annual_consolidated",
            "financial_results_quarterly_standalone",
            "financial_results_annual_standalone",
            "net_profit_standalone",
        ]
        return self.get_sections(symbol, fields, ensure=True)

    def get_latest_news_bundle(self, symbol: str) -> Optional[Dict[str, Any]]:
        fields = [
            "announcements",
            "company_filings_data",
            "live_news_data",
        ]
        return self.get_sections(symbol, fields, ensure=True)

    def get_mutual_fund_bundle(self, symbol: str) -> Optional[Dict[str, Any]]:
        fields = [
            "formatted_mutual_fund_holdings_data",
            "formatted_mutual_fund_transaction_data",
        ]
        return self.get_sections(symbol, fields, ensure=True)

    def get_corporate_bundle(self, symbol: str) -> Optional[Dict[str, Any]]:
        fields = [
            "corporate_action_data",
            "dividend_data",
        ]
        return self.get_sections(symbol, fields, ensure=True)

    def get_forecast(self, symbol: str, period: str) -> Optional[Any]:
        if period.upper() == "Q":
            return self.get_section(symbol, "forecast_data_Q", ensure=True)
        if period.upper() == "A":
            return self.get_section(symbol, "forecast_data_A", ensure=True)
        return None
