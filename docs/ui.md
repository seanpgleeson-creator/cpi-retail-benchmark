# User Interface Design Analysis

## Overview

This CPI Data system provides an interactive web-based interface that allows users to select multiple retailers and BLS product groups to analyze price change patterns relative to official BLS data. The system serves data analysts, researchers, and business users who need to understand how retail pricing tracks against government inflation indices.

## Primary Interface: Interactive Web Dashboard

### Main Interface Components

#### 1. **Retailer Selection Panel**

**Multi-Select Retailer Interface:**
```
┌─────────────────────────────────────────┐
│ Select Retailers                        │
├─────────────────────────────────────────┤
│ ☑ Target                               │
│ ☐ Walmart                              │
│ ☐ Kroger                               │
│ ☐ Safeway                              │
│ ☐ Costco                               │
│ ☐ Whole Foods                          │
│                                         │
│ [Select All] [Clear All]               │
└─────────────────────────────────────────┘
```

**Features:**
- Multi-select checkboxes for retailers
- Visual indicators for data availability per retailer
- Last data update timestamps
- Geographic coverage indicators (ZIP codes/regions supported)

#### 2. **BLS Product Group Selection**

**Hierarchical Product Categories:**
```
┌─────────────────────────────────────────┐
│ BLS Product Categories                  │
├─────────────────────────────────────────┤
│ Food and Beverages                      │
│   ☑ Dairy and Related Products         │
│     ☑ Milk (APU0000709112)            │
│     ☐ Cheese (APU0000710111)          │
│     ☐ Ice Cream (APU0000710211)       │
│   ☐ Meat, Poultry, Fish & Eggs        │
│     ☐ Ground Beef (APU0000703112)     │
│     ☐ Chicken Breast (APU0000706111)  │
│   ☐ Fruits and Vegetables             │
│     ☐ Apples (APU0000711111)          │
│     ☐ Bananas (APU0000711311)         │
│                                         │
│ Housing                                 │
│   ☐ Rent                              │
│   ☐ Utilities                         │
│                                         │
│ [Expand All] [Collapse All]           │
└─────────────────────────────────────────┘
```

**Features:**
- Hierarchical tree structure matching BLS organization
- Series ID display for technical users
- Category descriptions and units (per gallon, per pound, etc.)
- Search functionality to find specific products

#### 3. **Time Period Selection**

**Date Range and Update Controls:**
```
┌─────────────────────────────────────────┐
│ Analysis Period                         │
├─────────────────────────────────────────┤
│ Data as of: Sep 2025 BLS Release       │
│ (Released: Oct 13, 2025 at 8:30 AM)   │
│                                         │
│ Comparison Period:                      │
│ From: [Jan 2024 ▼] To: [Sep 2025 ▼]   │
│                                         │
│ Analysis Type:                          │
│ ○ Month-over-Month Changes             │
│ ○ Year-over-Year Changes               │
│ ☑ Both MoM and YoY                     │
│                                         │
│ [🔄 Refresh Data] [📊 Generate Report] │
└─────────────────────────────────────────┘
```

#### 4. **Geographic Selection**

**Location-Based Analysis:**
```
┌─────────────────────────────────────────┐
│ Geographic Scope                        │
├─────────────────────────────────────────┤
│ Analysis Level:                         │
│ ○ National Average                     │
│ ☑ Metro Area Specific                 │
│ ○ ZIP Code Level                       │
│                                         │
│ Selected Regions:                       │
│ ☑ Minneapolis-St. Paul (55331)        │
│ ☐ Chicago-Naperville (60601)          │
│ ☐ Los Angeles-Long Beach (90210)      │
│ ☐ New York-Newark (10001)             │
│                                         │
│ [Add Region] [Remove Selected]         │
└─────────────────────────────────────────┘
```

### Data Visualization Dashboard

#### 1. **Comparison Summary Cards**

**Key Metrics Overview:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ Price Change Comparison - September 2025                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Target vs BLS Milk Prices                                        │
│  ┌─────────────────┬──────────────┬─────────────┬─────────────────┐ │
│  │ Metric          │ Target       │ BLS         │ Difference      │ │
│  ├─────────────────┼──────────────┼─────────────┼─────────────────┤ │
│  │ Current Price   │ $3.99/gal    │ $4.17/gal   │ -$0.18 (-4.3%) │ │
│  │ MoM Change      │ +0.7%        │ +0.2%       │ +0.5pp 🔺      │ │
│  │ YoY Change      │ -1.2%        │ +3.7%       │ -4.9pp 🔻      │ │
│  └─────────────────┴──────────────┴─────────────┴─────────────────┘ │
│                                                                     │
│  VERDICT: Target pricing ABOVE BLS trend (MoM) 🔺                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 2. **Interactive Time Series Charts**

**Price Trend Visualization:**
```
Price Trends: Target vs BLS Milk (Last 24 Months)
┌─────────────────────────────────────────────────────────────────────┐
│ $5.00 ┤                                                             │
│       │     ●●●                                                     │
│ $4.50 ┤   ●●   ●●                                                   │
│       │ ●●       ●●  BLS Average Price (APU0000709112)             │
│ $4.00 ┤●           ●●●●●●●●●●●●●●●●●●●●●●●                        │
│       │                                                             │
│ $3.50 ┤              ■■■■■■■■■■■■■■■■■■■■■■■                      │
│       │            ■■         Target Average                       │
│ $3.00 ┤          ■■                                                 │
│       │        ■■                                                   │
│ $2.50 ┤      ■■                                                     │
│       └─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬───────│
│           Jan24  Apr24  Jul24  Oct24  Jan25  Apr25  Jul25  Sep25    │
└─────────────────────────────────────────────────────────────────────┘

[📊 Switch to Bar Chart] [📈 Show Percentage Changes] [💾 Export Chart]
```

#### 3. **Multi-Retailer Comparison Matrix**

**Retailer Performance Grid:**
```
┌─────────────────────────────────────────────────────────────────────┐
│ Multi-Retailer Analysis: Dairy Products (Sep 2025)                 │
├─────────────────────────────────────────────────────────────────────┤
│                    │ Current  │ MoM    │ YoY    │ vs BLS  │ Trend   │
│                    │ Price    │ Change │ Change │ Gap     │ Status  │
├────────────────────┼──────────┼────────┼────────┼─────────┼─────────┤
│ Target             │ $3.99    │ +0.7%  │ -1.2%  │ -4.3%   │ ABOVE🔺 │
│ Walmart            │ $3.89    │ +0.3%  │ -0.8%  │ -6.7%   │ INLINE  │
│ Kroger             │ $4.29    │ +0.9%  │ +2.1%  │ +2.9%   │ ABOVE🔺 │
│ Whole Foods        │ $5.49    │ +0.5%  │ +1.8%  │ +31.7%  │ ABOVE🔺 │
├────────────────────┼──────────┼────────┼────────┼─────────┼─────────┤
│ BLS Benchmark      │ $4.17    │ +0.2%  │ +3.7%  │ --      │ --      │
└─────────────────────────────────────────────────────────────────────┘

🔺 Above BLS trend  ⚪ Inline with BLS  🔻 Below BLS trend
```

#### 4. **Product Category Heatmap**

**Cross-Category Analysis:**
```
Price Change Heatmap: Food Categories vs BLS (MoM %)
┌─────────────────────────────────────────────────────────────────────┐
│              │Target│Walmart│Kroger│Costco│ BLS │ Avg Gap │
├──────────────┼──────┼───────┼──────┼──────┼─────┼─────────┤
│ Milk         │ +0.7 │ +0.3  │ +0.9 │ +0.4 │+0.2 │ +0.4pp  │ 🔴
│ Cheese       │ +1.2 │ +0.8  │ +1.5 │ +0.9 │+0.6 │ +0.7pp  │ 🔴
│ Ground Beef  │ -0.3 │ -0.8  │ +0.1 │ -0.5 │+0.1 │ -0.4pp  │ 🔵
│ Chicken      │ +0.9 │ +0.4  │ +1.1 │ +0.6 │+0.3 │ +0.5pp  │ 🔴
│ Bread        │ +0.5 │ +0.2  │ +0.7 │ +0.3 │+0.4 │ +0.1pp  │ 🟡
└─────────────────────────────────────────────────────────────────────┘

🔴 Above BLS (+0.2pp)  🟡 Inline (±0.2pp)  🔵 Below BLS (-0.2pp)
```

### Interactive Features

#### 1. **Dynamic Filtering and Drill-Down**
- Click on any retailer to see detailed store-level data
- Filter by date ranges with slider controls
- Toggle between different BLS series for comparison
- Geographic filtering with interactive map

#### 2. **Export and Sharing Options**
```
┌─────────────────────────────────────────┐
│ Export Options                          │
├─────────────────────────────────────────┤
│ 📊 Charts                              │
│   ☐ PNG (high-res)                    │
│   ☐ SVG (vector)                      │
│   ☐ PDF report                        │
│                                         │
│ 📋 Data                                │
│   ☐ CSV (raw data)                    │
│   ☐ Excel (formatted)                 │
│   ☐ JSON (API format)                 │
│                                         │
│ 🔗 Sharing                            │
│   ☐ Shareable URL                     │
│   ☐ Email report                      │
│   ☐ Schedule updates                  │
│                                         │
│ [Generate Export] [Cancel]             │
└─────────────────────────────────────────┘
```

#### 3. **Real-Time Updates and Notifications**
- Auto-refresh when new BLS data is released
- Browser notifications for significant price changes
- Email alerts for custom thresholds
- RSS feed for automated monitoring

### User Experience Features

#### 1. **Progressive Disclosure**
- **Summary View**: High-level comparison cards
- **Detailed View**: Full time series and breakdowns
- **Advanced View**: Technical details, series IDs, methodology

#### 2. **Contextual Help**
- Hover tooltips explaining BLS methodology
- "What does this mean?" explanations for verdicts
- Links to BLS documentation and data sources
- Glossary of terms (MoM, YoY, pp, etc.)

#### 3. **Responsive Design**
- Mobile-optimized charts and tables
- Touch-friendly controls
- Adaptive layouts for different screen sizes
- Offline mode for cached data viewing

#### 4. **Error Handling & User Feedback**

**Data Quality Indicators:**
```
┌─────────────────────────────────────────┐
│ Data Status                             │
├─────────────────────────────────────────┤
│ BLS Data: ✅ Current (Oct 13, 2025)    │
│ Target: ✅ Updated (Oct 15, 2025)      │
│ Walmart: ⚠️ Stale (Oct 10, 2025)      │
│ Kroger: ❌ No recent data              │
│                                         │
│ [Refresh All] [View Details]           │
└─────────────────────────────────────────┘
```

**Error Messages:**
- **No Data Available**: "No price data found for selected retailers and time period. Try expanding the date range."
- **BLS Service Interruption**: "BLS data temporarily unavailable. Showing last known values from [date]."
- **Incomplete Coverage**: "Limited data available for this region. Results may not be representative."

### Alert and Notification System

#### 1. **Custom Alerts Setup**
```
┌─────────────────────────────────────────┐
│ Create Price Alert                      │
├─────────────────────────────────────────┤
│ Alert Name: [Milk Price Divergence]    │
│                                         │
│ Trigger Conditions:                     │
│ ☑ MoM difference > 0.5pp               │
│ ☐ YoY difference > 2.0pp               │
│ ☐ Price gap > 10%                      │
│                                         │
│ Retailers: [Target ▼] [+ Add More]     │
│ Products: [Milk ▼] [+ Add More]        │
│                                         │
│ Notification Method:                    │
│ ☑ Email: user@example.com             │
│ ☐ SMS: +1 (555) 123-4567              │
│ ☐ Slack: #pricing-alerts              │
│                                         │
│ [Save Alert] [Test] [Cancel]           │
└─────────────────────────────────────────┘
```

## Output Formats

### 1. **CSV Export Format**
```csv
month,zip_code,target_avg_price,target_mom,target_yoy,bls_avg_price,bls_mom,bls_yoy,price_gap,mom_diff,verdict
2025-09,55331,3.99,0.7,-1.2,4.17,0.2,3.7,-0.18,0.5,Target ABOVE BLS (MoM)
```

### 2. **JSON Export Format**
```json
{
  "month": "2025-09",
  "zip_code": "55331",
  "target": {
    "avg_price_per_gal": 3.99,
    "mom_change_pct": 0.7,
    "yoy_change_pct": -1.2,
    "basket_size": 2,
    "skus": ["Good & Gather 1 Gal", "Kemps 1 Gal"]
  },
  "bls": {
    "avg_price_per_gal": 4.17,
    "mom_change_pct": 0.2,
    "yoy_change_pct": 3.7,
    "series_id": "APU0000709112"
  },
  "comparison": {
    "price_gap": -0.18,
    "mom_difference_pp": 0.5,
    "yoy_difference_pp": -4.9,
    "verdict": "Target ABOVE BLS (MoM)"
  }
}
```

### 3. **Table Format** (for compare --format table)
```
┌─────────────┬──────────────┬─────────────┬─────────────┐
│ Metric      │ Target       │ BLS         │ Difference  │
├─────────────┼──────────────┼─────────────┼─────────────┤
│ Price/Gal   │ $3.99        │ $4.17       │ -$0.18      │
│ MoM Change  │ +0.7%        │ +0.2%       │ +0.5pp      │
│ YoY Change  │ -1.2%        │ +3.7%       │ -4.9pp      │
└─────────────┴──────────────┴─────────────┴─────────────┘
Verdict: Target ABOVE BLS month-over-month trend
```

## Configuration Interface

### Environment Variables (.env)
```bash
# API Configuration
BLS_API_KEY=optional_key_for_higher_limits
ZIP_CODE=55331

# Scraping Configuration  
HEADLESS=true
SCRAPE_MAX_PAGES=5
SCRAPE_DELAY_RANGE_MS=500-1500

# Database
DATABASE_URL=sqlite:///data/cpi_benchmark.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### CLI Configuration Override
```bash
# Override via command line
python app.py scrape --zip 90210 --max-pages 10 --headless false
```

## User Experience Considerations

### 1. **Progressive Disclosure**
- Commands show minimal output by default
- Use `--verbose` for detailed operational logs
- Use `--quiet` for automation/cron jobs

### 2. **Graceful Degradation**
- Continue with cached BLS data if API is unavailable
- Warn but proceed if some Target products are out of stock
- Provide partial results if scraping is interrupted

### 3. **Data Validation Feedback**
- Clear messages for invalid ZIP codes, dates, or series IDs
- Suggestions for common mistakes ("Did you mean 55331?")
- Links to BLS documentation for series ID lookup

### 4. **Automation-Friendly**
- Consistent exit codes (0=success, 1=error, 2=warning)
- Machine-readable JSON output option
- Silent mode for cron jobs

### 5. **Documentation Integration**
- Built-in help with examples: `python app.py scrape --help`
- Links to README for setup instructions
- BLS series ID reference table in help text

## Scheduled Automation Interface

### tasks.yaml Structure
```yaml
# Suggested cron schedules
monthly_scrape:
  command: "python app.py scrape --zip 55331"
  schedule: "0 2 28-31 * *"  # Last 4 days of month at 2 AM
  description: "Monthly Target milk price scrape"

basket_build:
  command: "python app.py build-basket --month $(date +%Y-%m)"
  schedule: "0 3 1 * *"  # 1st of month at 3 AM
  description: "Build monthly basket from latest scrape"

bls_update:
  command: "python app.py bls-pull"
  schedule: "0 10 13 * *"  # 13th of month at 10 AM (typical CPI release)
  description: "Pull latest BLS CPI data"

monthly_report:
  command: "python app.py compare --month $(date +%Y-%m) > reports/$(date +%Y-%m).txt"
  schedule: "0 11 13 * *"  # After BLS update
  description: "Generate monthly comparison report"
```

## Future UI Enhancements (Beyond MVP)

### 1. **Web Dashboard** (Optional)
- Simple Flask/Streamlit app for non-technical users
- Charts showing price trends over time
- Interactive ZIP code selection

### 2. **API Interface** (Optional)
- REST endpoints for programmatic access
- JSON responses for integration with other tools

### 3. **Notification System** (Optional)
- Email alerts for significant price divergences
- Slack/Teams integration for team reporting

This UI design prioritizes clarity, automation-friendliness, and robust error handling while maintaining the simplicity appropriate for an MVP focused on data analysis workflows.
