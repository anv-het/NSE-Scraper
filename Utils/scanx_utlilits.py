import concurrent.futures

FIELD_MAPPINGS = {

    "bs_c": {
        "CURRENT_ASSETS": "Current Assets",
        "CURRENT_LIABILITIES": "Current Liabilities",
        "CWIP": "CWIP",
        "FIXED_ASSETS": "Fixed Assets",
        "INVESTMENTS": "Investments",
        "MINORITY_INTEREST": "Minority Interest",
        "NON_CURRENT_LIABILITIES": "Non-current Liabilities",
        "OTHER_ASSETS": "Other Assets",
        "RESERVE_SURPLUS": "Reserve & Surplus",
        "SHAREHOLDERs_CAPITAL": "Shareholders' Capital",
        "SHARE_CAPITAL": "Share Capital",
        "TOTAL_ASSETS": "Total Assets",
        "TOTAL_EQUITY": "Total Equity",
        "TOTAL_EQUITY_AND_LIABILITIES": "Total Equity & Liabilities",
        "YEAR": "Year"
    },

    "bs_s": {
        "CURRENT_ASSETS": "Current Assets",
        "CURRENT_LIABILITIES": "Current Liabilities",
        "CWIP": "CWIP",
        "FIXED_ASSETS": "Fixed Assets",
        "INVESTMENTS": "Investments",
        "MINORITY_INTEREST": "Minority Interest",
        "NON_CURRENT_LIABILITIES": "Non-current Liabilities",
        "OTHER_ASSETS": "Other Assets",
        "RESERVE_SURPLUS": "Reserve & Surplus",
        "SHAREHOLDERs_CAPITAL": "Shareholders' Capital",
        "SHARE_CAPITAL": "Share Capital",
        "TOTAL_ASSETS": "Total Assets",
        "TOTAL_EQUITY": "Total Equity",
        "TOTAL_EQUITY_AND_LIABILITIES": "Total Equity & Liabilities",
        "YEAR": "Year"
    },

    "cF_c": {
        "CAPITAL_EXPENDITURE": "Capital Expenditure",
        "CHANGES_IN_WORKING_CAPITAL": "Changes in Working Capital",
        "FINANCING_ACTIVITIES": "Financing Activities",
        "INVESTING_ACTIVITIES": "Investing Activities",
        "NET_CASH_FLOW": "Net Cash Flow",
        "OPERATING_ACTIVITIES": "Operating Activities",
        "YEAR": "Year"
    },

    "cF_s": {
        "CAPITAL_EXPENDITURE": "Capital Expenditure",
        "CHANGES_IN_WORKING_CAPITAL": "Changes in Working Capital",
        "FINANCING_ACTIVITIES": "Financing Activities",
        "INVESTING_ACTIVITIES": "Investing Activities",
        "NET_CASH_FLOW": "Net Cash Flow",
        "OPERATING_ACTIVITIES": "Operating Activities",
        "YEAR": "Year"
    },
    
    "incomeStat_cq": {
        "DEPRECIATION": "Depreciation",
        "EBITDA": "EBITDA",
        "EPS": "EPS",
        "INTEREST": "Interest",
        "EXPENSES": "Expenses",
        "NET_PROFIT": "Net Profit",
        "OPM": "Operating Profit Margin",
        "OPERATING_PROFIT": "Operating Profit",
        "OTHER_INCOME": "Other Income",
        "PROFIT_BEFORE_TAX": "Profit Before Tax",
        "REVENUE": "Revenue",
        "SALES": "Sales",
        "TAX": "Tax %",
        "TAX_PAYMENT_ABSOLUTE": "Tax Paid",
        "YEAR": "Year"
    },

    "incomeStat_cy": {
        "DEPRECIATION": "Depreciation",
        "EBITDA": "EBITDA",
        "EPS": "EPS",
        "INTEREST": "Interest",
        "EXPENSES": "Expenses",
        "NET_PROFIT": "Net Profit",
        "OPM": "Operating Profit Margin",
        "OPERATING_PROFIT": "Operating Profit",
        "OTHER_INCOME": "Other Income",
        "PROFIT_BEFORE_TAX": "Profit Before Tax",
        "REVENUE": "Revenue",
        "SALES": "Sales",
        "TAX": "Tax %",
        "TAX_PAYMENT_ABSOLUTE": "Tax Paid",
        "YEAR": "Year"
    },
    
    "incomeStat_sq": {
        "DEPRECIATION": "Depreciation",
        "EBITDA": "EBITDA",
        "EPS": "EPS",
        "INTEREST": "Interest",
        "EXPENSES": "Expenses",
        "NET_PROFIT": "Net Profit",
        "OPM": "Operating Profit Margin",
        "OPERATING_PROFIT": "Operating Profit",
        "OTHER_INCOME": "Other Income",
        "PROFIT_BEFORE_TAX": "Profit Before Tax",
        "REVENUE": "Revenue",
        "SALES": "Sales",
        "TAX": "Tax %",
        "TAX_PAYMENT_ABSOLUTE": "Tax Paid",
        "YEAR": "Year"
    },

    "incomeStat_sy": {
        "DEPRECIATION": "Depreciation",
        "EBITDA": "EBITDA",
        "EPS": "EPS",
        "INTEREST": "Interest",
        "EXPENSES": "Expenses",
        "NET_PROFIT": "Net Profit",
        "OPM": "Operating Profit Margin",
        "OPERATING_PROFIT": "Operating Profit",
        "OTHER_INCOME": "Other Income",
        "PROFIT_BEFORE_TAX": "Profit Before Tax",
        "REVENUE": "Revenue",
        "SALES": "Sales",
        "TAX": "Tax %",
        "TAX_PAYMENT_ABSOLUTE": "Tax Paid",
        "YEAR": "Year"
    },

    "rNp_s":{
        "PROFIT": "Profit",
        "PROFIT_GROWTH": "Profit Growth",
        "REVENUE": "Revenue",
        "REVENUE_GROWTH": "Revenue Growth",
        "YEAR": "Year"
    },
    
    "sHp": {
        "DII": "Domestic Institutional Investors",
        "FII": "Foreign Institutional Investors",
        "GOVERNMENT": "Government",
        "NO_OF_SHARE_HOLDERS": "Number of Shareholders",
        "OTHERS": "Others",
        "PROMOTER": "PROMOTER",
        "PUBLIC": "Public",
        "YEAR": "Year"
    }
}


ABOUT_COMPANY_API_URL = 'https://scanx-analytics.dhan.co/customscan/fetchdt'
ANALYST_RATING_API_URL = 'https://static-scanx.dhan.co/staticscanx/analyst_rating'
ANNOUNCEMENTS_API_URL = 'https://static-scanx.dhan.co/staticscanx/lodr'
LATEST_NEW_ANNOUNCEMENT_API_URL = 'https://static-scanx.dhan.co/staticscanx/announcements'
LIVE_NEWS_API_URL = 'https://news-live.dhan.co/v3/news/getLiveNews'
DIVIDEND_DATA_API_URL = 'https://static-scanx.dhan.co/staticscanx/dividenddata'
FUNDAMENTAL_DATA_API_URL = 'https://scanx.dhan.co/scanx/fundamental'
FORECAST_DATA_API_URL = 'https://static-scanx.dhan.co/staticscanx/forecast'
CORPORATE_ACTION_API_URL = 'https://static-scanx.dhan.co/staticscanx/corporate_action'
COMPANY_FILINGS_API_URL = 'https://static-scanx.dhan.co/staticscanx/company_filings'
MUTUAL_FUND_HOLDINGS_API_URL = 'https://static-scanx.dhan.co/staticscanx/mfpastholdingsbyisin'
LAST_FIVE_YEARS_CHART_DATA_API_URL = 'https://openweb-ticks.dhan.co/getDataH'
MULTI_TIMEFRAME_CHART_DATA_API_URL = 'https://open-web-scanx.dhan.co/scanx/multirtscrdt'
MUTUAL_FUND_TRANSACTION_API_URL = 'https://static-scanx.dhan.co/staticscanx/mftransaction'


def parallel_format_financial_data(raw_data: dict, report_type: str) -> list:
    field_map = FIELD_MAPPINGS.get(report_type)
    if not field_map:
        raise ValueError(f"Invalid report_type '{report_type}'")

    years = raw_data.get("YEAR", "").split("|")
    formatted_years = [
        f"{y[:4]}-{y[4:]}" if len(y) == 6 else y for y in years
    ]

    parsed_data = {
        label: raw_data.get(key, "").split("|")
        for key, label in field_map.items()
        if key != "YEAR"
    }

    def build_entry(idx):
        entry = {"year": formatted_years[idx]}
        for label, values in parsed_data.items():
            try:
                entry[label] = float(values[idx]) if idx < len(values) else None
            except (ValueError, TypeError):
                entry[label] = None
        return entry

    with concurrent.futures.ThreadPoolExecutor() as executor:
        output = list(executor.map(build_entry, range(len(formatted_years))))

    return output

def parallel_format_quarterly_data(income_stat_cq):
    field_map = {
        "DEPRECIATION": "Depreciation",
        "EBITDA": "EBITDA",
        "EPS": "EPS",
        "INTEREST": "Interest",
        "EXPENSES": "Expenses",
        "NET_PROFIT": "Net Profit",
        "OPM": "Operating Profit",
        "OPERATING_PROFIT": "Operating Profit",
        "OTHER_INCOME": "Other Income",
        "PROFIT_BEFORE_TAX": "Profit Before Tax",
        "REVENUE": "Revenue",
        "SALES": "Sales",
        "TAX": "Tax_percentage",
        "TAX_PAYMENT_ABSOLUTE": "Tax Payment Absolute"
    }

    year_raw = income_stat_cq["YEAR"]
    years = year_raw.split("|")

    parsed_data = {}
    for key, label in field_map.items():
        raw_values = income_stat_cq.get(key, "")
        parsed_data[label] = raw_values.split("|")

    def build_entry(idx):
        year_val = years[idx]
        year_formatted = f"{year_val[:4]}-{year_val[4:]}"
        entry = {"year": year_formatted}
        for label in field_map.values():
            values = parsed_data[label]
            if idx < len(values):
                try:
                    entry[label] = float(values[idx])
                except ValueError:
                    entry[label] = None
            else:
                entry[label] = None
        return entry

    with concurrent.futures.ThreadPoolExecutor() as executor:
        formatted_output = list(executor.map(build_entry, range(len(years))))

    return formatted_output

def parallel_format_stock_chart_data(raw_data) -> dict:
    formatted_output = {}

    def process_stock(stock_name, stock_info):
        if not isinstance(stock_info, dict) or not stock_info.get("success"):
            return stock_name, []
        data = stock_info.get("data", {})
        dates = data.get("Time", [])
        opens = data.get("o", [])
        closes = data.get("c", [])
        highs = data.get("h", [])
        lows = data.get("l", [])
        volumes = data.get("v", [])
        delivery_percents = data.get("delivery_per", [])
        open_interests = data.get("oi", [])
        max_len = len(dates)
        chart_data = []
        for i in range(max_len):
            chart_entry = {
                "date": dates[i] if i < len(dates) else None,
                "open": opens[i] if i < len(opens) else None,
                "close": closes[i] if i < len(closes) else None,
                "high": highs[i] if i < len(highs) else None,
                "low": lows[i] if i < len(lows) else None,
                "volume": volumes[i] if i < len(volumes) else None,
                "open_interest": open_interests[i] if i < len(open_interests) else None,
                "delivery_per": delivery_percents[i] if i < len(delivery_percents) else None,
            }
            chart_data.append(chart_entry)
        return stock_name, chart_data

    if isinstance(raw_data, dict):
        items = list(raw_data.items())
    elif isinstance(raw_data, list):
        items = []
        for entry in raw_data:
            if not isinstance(entry, dict):
                continue
            peer_data = entry.get("last_five_years_chart_data_peer", {})
            items.extend(peer_data.items())
    else:
        items = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda args: process_stock(*args), items))

    for stock_name, chart_data in results:
        formatted_output[stock_name] = chart_data

    return formatted_output

def optimize_format_mutual_fund_data(raw_data):
    if not isinstance(raw_data, dict) or "data" not in raw_data:
        return []

    def format_entry(entry):
        if len(entry) == 9:
            return {
                "mf_id": entry[0],
                "mf_name": entry[1],
                "mf_uniqe": entry[2],
                "Net Quantity": entry[3],
                "Net Value": entry[4],
                "isin": entry[5],
                "action": entry[6],
                "month": entry[7],
                "url_end_point": entry[8]
            }
        elif len(entry) == 11:  # ✅ Fixed from >=13 to ==11
            qty_list = entry[4].split("|")
            perc_list = entry[5].split("|")
            date_list = entry[9].split("|")

            past_holding = [
                {"qty_holding": qty, "percentage_cng": perc, "date": date}
                for qty, perc, date in zip(qty_list, perc_list, date_list)
            ]

            return {
                "mf_id": entry[0],
                "mf_name": entry[1],
                "mf_uniqe": entry[2],
                "isin": entry[3],
                "past_holding": past_holding,
                "1M_change_qty": entry[6],
                "1M_change_per": entry[7],
                "3M_change_per": entry[8],
                "current_holding_perc": perc_list[0] if perc_list else None,
                "current_holding_qty": qty_list[0] if qty_list else None,
                "url_end_point": entry[10]
            }

        return None

    return [
        result for entry in raw_data["data"]
        if (result := format_entry(entry)) is not None
    ]



def parallel_format_financial_data(raw_data: dict, report_type: str) -> list:
    field_map = FIELD_MAPPINGS.get(report_type)
    if not field_map:
        raise ValueError(f"Invalid report_type '{report_type}'")

    years = raw_data.get("YEAR", "").split("|")
    formatted_years = [
        f"{y[:4]}-{y[4:]}" if len(y) == 6 else y for y in years
    ]

    parsed_data = {
        label: raw_data.get(key, "").split("|")
        for key, label in field_map.items()
        if key != "YEAR"
    }

    def build_entry(idx):
        entry = {"year": formatted_years[idx]}
        for label, values in parsed_data.items():
            try:
                entry[label] = float(values[idx]) if idx < len(values) else None
            except (ValueError, TypeError):
                entry[label] = None
        return entry

    with concurrent.futures.ThreadPoolExecutor() as executor:
        output = list(executor.map(build_entry, range(len(formatted_years))))

    return output

def parallel_format_quarterly_data(income_stat_cq):
    field_map = {
        "DEPRECIATION": "Depreciation",
        "EBITDA": "EBITDA",
        "EPS": "EPS",
        "INTEREST": "Interest",
        "EXPENSES": "Expenses",
        "NET_PROFIT": "Net Profit",
        "OPM": "Operating Profit",
        "OPERATING_PROFIT": "Operating Profit",
        "OTHER_INCOME": "Other Income",
        "PROFIT_BEFORE_TAX": "Profit Before Tax",
        "REVENUE": "Revenue",
        "SALES": "Sales",
        "TAX": "Tax_percentage",
        "TAX_PAYMENT_ABSOLUTE": "Tax Payment Absolute"
    }

    year_raw = income_stat_cq["YEAR"]
    years = year_raw.split("|")

    parsed_data = {}
    for key, label in field_map.items():
        raw_values = income_stat_cq.get(key, "")
        parsed_data[label] = raw_values.split("|")

    def build_entry(idx):
        year_val = years[idx]
        year_formatted = f"{year_val[:4]}-{year_val[4:]}"
        entry = {"year": year_formatted}
        for label in field_map.values():
            values = parsed_data[label]
            if idx < len(values):
                try:
                    entry[label] = float(values[idx])
                except ValueError:
                    entry[label] = None
            else:
                entry[label] = None
        return entry

    with concurrent.futures.ThreadPoolExecutor() as executor:
        formatted_output = list(executor.map(build_entry, range(len(years))))

    return formatted_output

def parallel_format_stock_chart_data(raw_data) -> dict:
    formatted_output = {}

    def process_stock(stock_name, stock_info):
        if not isinstance(stock_info, dict) or not stock_info.get("success"):
            return stock_name, []
        data = stock_info.get("data", {})
        dates = data.get("Time", [])
        opens = data.get("o", [])
        closes = data.get("c", [])
        highs = data.get("h", [])
        lows = data.get("l", [])
        volumes = data.get("v", [])
        delivery_percents = data.get("delivery_per", [])
        open_interests = data.get("oi", [])
        max_len = len(dates)
        chart_data = []
        for i in range(max_len):
            chart_entry = {
                "date": dates[i] if i < len(dates) else None,
                "open": opens[i] if i < len(opens) else None,
                "close": closes[i] if i < len(closes) else None,
                "high": highs[i] if i < len(highs) else None,
                "low": lows[i] if i < len(lows) else None,
                "volume": volumes[i] if i < len(volumes) else None,
                "open_interest": open_interests[i] if i < len(open_interests) else None,
                "delivery_per": delivery_percents[i] if i < len(delivery_percents) else None,
            }
            chart_data.append(chart_entry)
        return stock_name, chart_data

    if isinstance(raw_data, dict):
        items = list(raw_data.items())
    elif isinstance(raw_data, list):
        items = []
        for entry in raw_data:
            if not isinstance(entry, dict):
                continue
            peer_data = entry.get("last_five_years_chart_data_peer", {})
            items.extend(peer_data.items())
    else:
        items = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda args: process_stock(*args), items))

    for stock_name, chart_data in results:
        formatted_output[stock_name] = chart_data

    return formatted_output

def optimize_format_mutual_fund_data(raw_data):
    if not isinstance(raw_data, dict) or "data" not in raw_data:
        return []

    def format_entry(entry):
        if len(entry) == 9:
            return {
                "mf_id": entry[0],
                "mf_name": entry[1],
                "mf_uniqe": entry[2],
                "Net Quantity": entry[3],
                "Net Value": entry[4],
                "isin": entry[5],
                "action": entry[6],
                "month": entry[7],
                "url_end_point": entry[8]
            }
        elif len(entry) == 11:  # ✅ Fixed from >=13 to ==11
            qty_list = entry[4].split("|")
            perc_list = entry[5].split("|")
            date_list = entry[9].split("|")

            past_holding = [
                {"qty_holding": qty, "percentage_cng": perc, "date": date}
                for qty, perc, date in zip(qty_list, perc_list, date_list)
            ]

            return {
                "mf_id": entry[0],
                "mf_name": entry[1],
                "mf_uniqe": entry[2],
                "isin": entry[3],
                "past_holding": past_holding,
                "1M_change_qty": entry[6],
                "1M_change_per": entry[7],
                "3M_change_per": entry[8],
                "current_holding_perc": perc_list[0] if perc_list else None,
                "current_holding_qty": qty_list[0] if qty_list else None,
                "url_end_point": entry[10]
            }

        return None

    return [
        result for entry in raw_data["data"]
        if (result := format_entry(entry)) is not None
    ]

# ==================================== Formation data Utilits ========================

def format_financial_data(raw_data: dict, report_type: str) -> list:
    # Fetch field mapping
    field_map = FIELD_MAPPINGS.get(report_type)
    if not field_map:
        raise ValueError(f"Invalid report_type '{report_type}'")

    # Extract and format years once
    years = raw_data.get("YEAR", "").split("|")
    formatted_years = [
        f"{y[:4]}-{y[4:]}" if len(y) == 6 else y for y in years
    ]

    # Pre-parse and cache all other field values
    parsed_data = {
        label: raw_data.get(key, "").split("|")
        for key, label in field_map.items()
        if key != "YEAR"
    }

    # Generate output efficiently
    output = []
    for idx, year in enumerate(formatted_years):
        entry = {"year": year}
        for label, values in parsed_data.items():
            try:
                entry[label] = float(values[idx]) if idx < len(values) else None
            except (ValueError, TypeError):
                entry[label] = None
        output.append(entry)

    return output

def format_quarterly_data(income_stat_cq):
    field_map = {
        "DEPRECIATION": "Depreciation",
        "EBITDA": "EBITDA",
        "EPS": "EPS",
        "INTEREST": "Interest",
        "EXPENSES": "Expenses",
        "NET_PROFIT": "Net Profit",
        "OPM": "Operating Profit",
        "OPERATING_PROFIT": "Operating Profit",
        "OTHER_INCOME": "Other Income",
        "PROFIT_BEFORE_TAX": "Profit Before Tax",
        "REVENUE": "Revenue",
        "SALES": "Sales",
        "TAX": "Tax_percentage",
        "TAX_PAYMENT_ABSOLUTE": "Tax Payment Absolute"
    }

                
    # Parse the year field
    year_raw = income_stat_cq["YEAR"]
    years = year_raw.split("|")

    # Create a dictionary to hold parsed field values
    parsed_data = {}

    for key, label in field_map.items():
        raw_values = income_stat_cq.get(key, "")
        parsed_data[label] = raw_values.split("|")

    formatted_output = []

    # Iterate over each index (assumes same length for all fields)
    for idx, year_val in enumerate(years):
        year_formatted = f"{year_val[:4]}-{year_val[4:]}"  # e.g., 202506 -> 2025-06
        entry = {"year": year_formatted}

        for label in field_map.values():
            values = parsed_data[label]
            if idx < len(values):
                try:
                    entry[label] = float(values[idx])
                except ValueError:
                    entry[label] = None  # Handle missing or corrupt values
            else:
                entry[label] = None

        formatted_output.append(entry)

    return formatted_output

def format_stock_chart_data(raw_data) -> dict:
    """
    Handles both:
    - a list of dicts with "last_five_years_chart_data_peer" key
    - a dict directly containing stock/index data
    """
    formatted_output = {}

    # If raw_data is a dict (stock/index data directly)
    if isinstance(raw_data, dict):
        peer_data = raw_data
        for stock_name, stock_info in peer_data.items():
            if not isinstance(stock_info, dict) or not stock_info.get("success"):
                continue

            data = stock_info.get("data", {})

            dates = data.get("Time", [])
            opens = data.get("o", [])
            closes = data.get("c", [])
            highs = data.get("h", [])
            lows = data.get("l", [])
            volumes = data.get("v", [])
            delivery_percents = data.get("delivery_per", [])
            open_interests = data.get("oi", [])

            chart_data = []
            max_len = len(dates)
            for i in range(max_len):
                chart_entry = {
                    "date": dates[i] if i < len(dates) else None,
                    "open": opens[i] if i < len(opens) else None,
                    "close": closes[i] if i < len(closes) else None,
                    "high": highs[i] if i < len(highs) else None,
                    "low": lows[i] if i < len(lows) else None,
                    "volume": volumes[i] if i < len(volumes) else None,
                    "open_interest": open_interests[i] if i < len(open_interests) else None,
                    "delivery_per": delivery_percents[i] if i < len(delivery_percents) else None,
                }
                chart_data.append(chart_entry)

            formatted_output[stock_name] = chart_data

    # If raw_data is a list (with "last_five_years_chart_data_peer" key)
    elif isinstance(raw_data, list):
        for entry in raw_data:
            if not isinstance(entry, dict):
                continue
            peer_data = entry.get("last_five_years_chart_data_peer", {})
            for stock_name, stock_info in peer_data.items():
                if not isinstance(stock_info, dict) or not stock_info.get("success"):
                    continue

                data = stock_info.get("data", {})

                dates = data.get("Time", [])
                opens = data.get("o", [])
                closes = data.get("c", [])
                highs = data.get("h", [])
                lows = data.get("l", [])
                volumes = data.get("v", [])
                delivery_percents = data.get("delivery_per", [])
                open_interests = data.get("oi", [])

                chart_data = []
                max_len = len(dates)
                for i in range(max_len):
                    chart_entry = {
                        "date": dates[i] if i < len(dates) else None,
                        "open": opens[i] if i < len(opens) else None,
                        "close": closes[i] if i < len(closes) else None,
                        "high": highs[i] if i < len(highs) else None,
                        "low": lows[i] if i < len(lows) else None,
                        "volume": volumes[i] if i < len(volumes) else None,
                        "open_interest": open_interests[i] if i < len(open_interests) else None,
                        "delivery_per": delivery_percents[i] if i < len(delivery_percents) else None,
                    }
                    chart_data.append(chart_entry)

                formatted_output[stock_name] = chart_data

    return formatted_output

def format_mutual_fund_data(raw_data):
    formatted_list = []
    if not isinstance(raw_data, dict) or "data" not in raw_data:
        return formatted_list

    for entry in raw_data["data"]:
        # First format type (short entry)
        if len(entry) == 9:
            formatted_list.append({
                "mf_id": entry[0],
                "mf_name": entry[1],
                "mf_uniqe": entry[2],
                "Net Quantity": entry[3],
                "Net Value": entry[4],
                "isin": entry[5],
                "action": entry[6],
                "month": entry[7],
                "url_end_point": entry[8]
            })
        # Second format type (long entry)
        elif len(entry) >= 13:
            qty_list = entry[4].split("|")
            perc_list = entry[5].split("|")
            date_list = entry[10].split("|")
            past_holding = []
            for qty, perc, date in zip(qty_list, perc_list, date_list):
                past_holding.append({
                    "qty_holding": qty,
                    "percentage_cng": perc,
                    "date": date
                })
            formatted_list.append({
                "mf_id": entry[0],
                "mf_name": entry[1],
                "mf_uniqe": entry[2],
                "isin": entry[3],
                "past_holding": past_holding,
                "1M_change_qty": entry[6],
                "1M_change_per": entry[7],
                "3M_change_per": entry[8],
                "current_holding_perc": perc_list[0] if perc_list else None,
                "current_holding_qty": qty_list[0] if qty_list else None,
                "url_end_point": entry[11]
            })
    return formatted_list

