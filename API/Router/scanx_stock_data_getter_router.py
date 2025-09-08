#!/usr/bin/env python3
"""
ScanX Stock Data Getter Router
==============================
FastAPI endpoints to retrieve ScanX stock data sections from MongoDB with on-demand scraping.

Patterns followed:
- Router structure similar to existing routers
- Uses response helpers and logger
- Normalizes symbol to uppercase

Contract:
- Input: symbol (query/path)
- Behavior: read from Mongo; if section missing, trigger single scrape once (per-symbol lock) and return
- Output: standardized success/error payload
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query

from Utils.logger import get_logger
from Utils.response import create_success_response_n, create_error_response
from API.Controller.scanx_stock_data_getter import ScanXStockDataGetterController


router = APIRouter()
logger = get_logger(__name__)


def _normalize_symbol(symbol: str) -> str:
    if not symbol:
        return symbol
    return symbol.strip().upper()


def _validate_symbol(symbol: str) -> str:
    """Validate and normalize symbol, raise HTTPException if invalid"""
    symbol = _normalize_symbol(symbol)
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol parameter is required")
    return symbol


def _wrap_data(endpoint: str, symbol: str, data: Any) -> Dict[str, Any]:
    return {
        "endpoint": endpoint,
        "symbol": symbol,
        "data": data,
    }


# 1. Company basic data
@router.get("/company/about_company")
def get_about_company(
    symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed"),
    include_outer: bool = Query(False, description="If true, returns the full document with about_company")
) -> Dict[str, Any]:
    """
    Return the `about_company` section for a symbol.

    Behavior:
    - DB-first: reads `scanx_stocks_data` collection for `about_company`.
    - If missing, triggers `scrape_single_symbol(symbol)` once (per-process lock).
    - If `include_outer=true`, returns the entire ensured document under key `outer`.

    Args:
        symbol: Stock symbol (required)
        include_outer: If true, include the full document

    Returns:
        Standardized response via `create_success_response_n` or error response.
    """
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        # Ensure doc present and then decide what to return
        doc = ctrl.get_sections(symbol, ["about_company"], ensure=True)
        if not doc:
            return create_error_response(message=f"No data for {symbol}")
        data = doc.get("about_company")
        payload = _wrap_data("about_company", symbol, data)
        if include_outer:
            payload["outer"] = doc
        return create_success_response_n(payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"about_company failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/analyst_ratings")
def get_analyst_ratings(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """
    Return analyst ratings for a symbol.

    Behavior: DB-first; triggers one-time scrape if data is missing.
    Args: symbol (required)
    Returns: standardized success/error response
    """
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "analyst_ratings", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("analyst_ratings", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"analyst_ratings failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 2. Company financial bundle
@router.get("/company/financials")
def get_financials(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """
    Return a bundle of financial sections for a symbol.

    Sections included:
    - balance_sheet_consolidated, balance_sheet_standalone
    - cash_flow_consolidated, cash_flow_standalone
    - quarterly/annual financial results (consolidated/standalone), net_profit_standalone

    Behavior: DB-first; triggers one-time scrape if missing.
    """
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_financials_bundle(symbol)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("financials", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"financials failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/balance_sheet_consolidated")
def balance_sheet_consolidated(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """
    Return consolidated balance sheet for a symbol.
    """
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "balance_sheet_consolidated", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("balance_sheet_consolidated", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"balance_sheet_consolidated failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/balance_sheet_standalone")
def balance_sheet_standalone(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """
    Return standalone balance sheet for a symbol.
    """
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "balance_sheet_standalone", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("balance_sheet_standalone", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"balance_sheet_standalone failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/cash_flow_consolidated")
def cash_flow_consolidated(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """
    Return consolidated cash flow for a symbol.
    """
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "cash_flow_consolidated", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("cash_flow_consolidated", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"cash_flow_consolidated failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/cash_flow_standalone")
def cash_flow_standalone(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """
    Return standalone cash flow for a symbol.
    """
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "cash_flow_standalone", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("cash_flow_standalone", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"cash_flow_standalone failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/financial_results_quarterly_consolidated")
def fr_q_c(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return quarterly consolidated financial results."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "financial_results_quarterly_consolidated", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("financial_results_quarterly_consolidated", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"financial_results_quarterly_consolidated failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/financial_results_annual_consolidated")
def fr_a_c(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return annual consolidated financial results."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "financial_results_annual_consolidated", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("financial_results_annual_consolidated", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"financial_results_annual_consolidated failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/financial_results_quarterly_standalone")
def fr_q_s(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return quarterly standalone financial results."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "financial_results_quarterly_standalone", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("financial_results_quarterly_standalone", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"financial_results_quarterly_standalone failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/financial_results_annual_standalone")
def fr_a_s(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return annual standalone financial results."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "financial_results_annual_standalone", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("financial_results_annual_standalone", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"financial_results_annual_standalone failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/net_profit_standalone")
def net_profit_standalone(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return standalone net profit series for a symbol."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "net_profit_standalone", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("net_profit_standalone", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"net_profit_standalone failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 3. Share holding
@router.get("/company/share_holders_equity")
def share_holders_equity(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return share holders equity/holding snapshot for a symbol."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "share_holders_equity", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("share_holders_equity", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"share_holders_equity failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 4. Mutual fund
@router.get("/mf/holdings")
def mf_holdings(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return formatted mutual fund holdings for a symbol."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "formatted_mutual_fund_holdings_data", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("formatted_mutual_fund_holdings_data", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"mf_holdings failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mf/transactions")
def mf_transactions(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return formatted mutual fund transactions for a symbol."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "formatted_mutual_fund_transaction_data", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("formatted_mutual_fund_transaction_data", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"mf_transactions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 5. Peer comparison
@router.get("/company/peer_comparison")
def peer_comparison(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return peer comparison list for the symbol's subsector/sector."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "peer_comparison", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("peer_comparison", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"peer_comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 6. Forecasts
@router.get("/company/forecast_Q")
def forecast_q(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return quarterly forecasts for the symbol."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_forecast(symbol, "Q")
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("forecast_data_Q", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"forecast_q failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/forecast_A")
def forecast_a(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return annual forecasts for the symbol."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_forecast(symbol, "A")
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("forecast_data_A", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"forecast_a failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 7. Corporate actions
@router.get("/company/corporate_action_data")
def corporate_action_data(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return corporate action history for the symbol."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "corporate_action_data", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("corporate_action_data", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"corporate_action_data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company/dividend_data")
def dividend_data(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return dividend records for the symbol."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "dividend_data", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("dividend_data", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"dividend_data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 8. Fundamentals
@router.get("/company/fundamental_data")
def fundamental_data(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return fundamental_data raw payload for the symbol."""
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "fundamental_data", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("fundamental_data", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"fundamental_data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 9. Latest news bundle
@router.get("/company/latest_news")
def latest_news(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_latest_news_bundle(symbol)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("latest_news", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"latest_news failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 10. Charts
@router.get("/charts/formatted_last_five_years_chart")
def charts_last_five_years(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    """Return preformatted last five years chart JSON for the symbol.

    Note: chart formatting can be expensive; the stored field `formatted_last_five_years_chart`
    is expected to be populated by `scrape_single_symbol` and stored in DB. If not present,
    the endpoint will trigger a scrape and then return the field if available.
    """
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "formatted_last_five_years_chart", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("formatted_last_five_years_chart", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"charts_last_five_years failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 9a. Announcements
@router.get("/company/announcements")
def announcements(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "announcements", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("announcements", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"announcements failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 9b. Company filings
@router.get("/company/company_filings_data")
def company_filings_data(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "company_filings_data", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("company_filings_data", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"company_filings_data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 9c. Live news
@router.get("/company/live_news_data")
def live_news_data(symbol: str = Query(None, description="Single stock symbol (e.g., 'TCS', 'INFY'), Index are not allowed")) -> Dict[str, Any]:
    try:
        symbol = _validate_symbol(symbol)
        ctrl = ScanXStockDataGetterController()
        data = ctrl.get_section(symbol, "live_news_data", ensure=True)
        if data is None:
            return create_error_response(message=f"No data for {symbol}")
        return create_success_response_n(_wrap_data("live_news_data", symbol, data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"live_news_data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
