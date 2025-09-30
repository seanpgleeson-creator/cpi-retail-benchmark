# Multi-Retailer CPI Price Benchmark Platform

[![Build Status](https://github.com/username/cpi-retail-benchmark/workflows/CI/badge.svg)](https://github.com/username/cpi-retail-benchmark/actions)
[![Coverage](https://codecov.io/gh/username/cpi-retail-benchmark/branch/main/graph/badge.svg)](https://codecov.io/gh/username/cpi-retail-benchmark)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive data analytics platform that tracks retail price changes across multiple retailers and compares them against Bureau of Labor Statistics (BLS) Consumer Price Index (CPI) data. Get real-time insights into how retail pricing patterns align with or diverge from official government inflation metrics.

## 🚀 Features

- **Multi-Retailer Tracking**: Daily price monitoring across Target, Walmart, Kroger, and other major retailers
- **BLS Integration**: Automatic synchronization with official government inflation data
- **Interactive Dashboard**: Web-based interface for exploring price trends and comparisons
- **Real-time Analysis**: Period-over-period comparison with automated verdict generation
- **Export & API**: Multiple export formats and programmatic access
- **Alert System**: Customizable notifications for significant price divergences

## 📊 How It Works

1. **Daily Data Collection**: Automated scraping of retailer prices with respect for robots.txt
2. **BLS Synchronization**: Monitoring of BLS data releases and automatic integration
3. **Period Aggregation**: Statistical analysis of price changes aligned with BLS release cycles
4. **Comparison Engine**: Delta analysis between retailer and government price trends
5. **Verdict Generation**: Automated classification (ABOVE/INLINE/BELOW) using ±0.2pp threshold

## 🛠️ Tech Stack

- **Backend**: Python 3.11, SQLAlchemy, Playwright, FastAPI
- **Frontend**: React/Next.js, Chart.js, Tailwind CSS
- **Database**: SQLite (upgradeable to PostgreSQL)
- **Deployment**: Vercel with GitHub Actions CI/CD
- **Data Sources**: BLS Public API, Retailer websites

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Git

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/username/cpi-retail-benchmark.git
cd cpi-retail-benchmark

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required variables:
# - BLS_API_KEY (optional but recommended)
# - ZIP_CODE (default: 55331)
# - DATABASE_URL (default: sqlite:///data/cpi_benchmark.db)
```

### 3. Database Setup

```bash
# Initialize database
python -m alembic upgrade head

# Optional: Load sample data
python scripts/load_sample_data.py
```

### 4. Run Development Server

```bash
# Start backend API
python -m uvicorn app.main:app --reload --port 8000

# In another terminal, start frontend (if using React)
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` for the web interface or `http://localhost:8000/docs` for API documentation.

## 📖 Usage

### Command Line Interface

```bash
# Scrape retailer data
python app.py scrape --retailer target --zip 55331

# Pull latest BLS data
python app.py bls-pull

# Generate comparison report
python app.py compare --month 2025-09

# Export data
python app.py export --month 2025-09 --format csv --output results.csv
```

### Web Interface

1. **Select Retailers**: Choose from Target, Walmart, Kroger, etc.
2. **Choose Products**: Select BLS product categories (milk, cheese, etc.)
3. **Set Geography**: Pick ZIP codes or metro areas
4. **Analyze**: View comparisons, charts, and trends
5. **Export**: Download data in CSV, Excel, or JSON formats

### API Usage

```python
import requests

# Get latest comparison data
response = requests.get("http://localhost:8000/api/v1/comparisons/latest")
data = response.json()

# Get retailer data for specific period
response = requests.get("http://localhost:8000/api/v1/retailers/target/prices", 
                       params={"zip_code": "55331", "period": "2025-09"})
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BLS_API_KEY` | Optional BLS API key for higher rate limits | None |
| `ZIP_CODE` | Default ZIP code for scraping | 55331 |
| `DATABASE_URL` | Database connection string | sqlite:///data/cpi_benchmark.db |
| `HEADLESS` | Run scrapers in headless mode | true |
| `SCRAPE_MAX_PAGES` | Maximum pages to scrape per session | 5 |
| `SCRAPE_DELAY_RANGE_MS` | Random delay range between requests | 500-1500 |
| `LOG_LEVEL` | Logging level | INFO |

### BLS Series IDs

| Product | Series ID | Description |
|---------|-----------|-------------|
| Milk (CPI-U) | CUUR0000SEFJ01 | CPI-U Milk, Not Seasonally Adjusted |
| Milk (CPI-U SA) | CUSR0000SEFJ01 | CPI-U Milk, Seasonally Adjusted |
| Milk (Avg Price) | APU0000709112 | Average Price: Milk, whole, per gallon |

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test files
pytest tests/test_bls_client.py
pytest tests/test_scrapers.py

# Run linting
flake8 app/
black app/
mypy app/
```

## 📦 Deployment

### Vercel Deployment

1. Connect your GitHub repository to Vercel
2. Configure environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

```bash
# Build and deploy
vercel build
vercel deploy
```

### Manual Deployment

```bash
# Build frontend
cd frontend && npm run build

# Run production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Respect robots.txt and implement ethical scraping practices

## 📝 Data Sources & Methodology

### BLS Data
- **Source**: Bureau of Labor Statistics Public API
- **Update Frequency**: Monthly (typically 2nd Tuesday)
- **Coverage**: National and regional price indices

### Retailer Data
- **Collection Method**: Automated web scraping with Playwright
- **Frequency**: Daily
- **Compliance**: Respects robots.txt, implements rate limiting
- **Coverage**: Major retailers across multiple ZIP codes

### Comparison Methodology
- **Period Definition**: Aligned with BLS release cycles
- **Aggregation**: Statistical analysis (mean, median, std dev)
- **Comparison**: Percentage point difference between price changes
- **Verdict Threshold**: ±0.2pp for "INLINE" classification

## ⚖️ Legal & Compliance

- Strict adherence to robots.txt files
- Respectful rate limiting and request spacing
- No circumvention of anti-bot measures
- Transparent methodology and data sources
- Option to switch to licensed data providers if needed

## 📞 Support

- **Documentation**: [Project Wiki](https://github.com/username/cpi-retail-benchmark/wiki)
- **Issues**: [GitHub Issues](https://github.com/username/cpi-retail-benchmark/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/cpi-retail-benchmark/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Bureau of Labor Statistics for providing public CPI data
- Playwright team for excellent web automation tools
- Open source community for foundational libraries

## 🗺️ Roadmap

- [ ] **Phase 1**: Core MVP with Target integration
- [ ] **Phase 2**: Multi-retailer expansion and web dashboard
- [ ] **Phase 3**: Advanced analytics and ML-powered insights
- [ ] **Phase 4**: Enterprise features and API partnerships

---

**Built with ❤️ for economic research and price transparency**
