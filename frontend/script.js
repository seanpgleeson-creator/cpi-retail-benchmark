// CPI Retail Benchmark Platform - Dashboard JavaScript

// Global state
let currentChart = null;
let apiBaseUrl = window.location.origin;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    loadDashboardData();
    setupEventListeners();
});

// Initialize dashboard components
function initializeDashboard() {
    console.log('Initializing CPI Retail Benchmark Dashboard');
    
    // Setup navigation
    setupNavigation();
    
    // Load initial status
    updateActivity('Dashboard initialized', 'info');
}

// Setup navigation between sections
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            const targetSection = link.getAttribute('data-section');
            
            // Update active nav link
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Show target section
            sections.forEach(s => s.classList.remove('active'));
            document.getElementById(targetSection).classList.add('active');
            
            // Load section-specific data
            loadSectionData(targetSection);
        });
    });
}

// Setup event listeners
function setupEventListeners() {
    // Category selection change
    const categorySelect = document.getElementById('category-select');
    if (categorySelect) {
        categorySelect.addEventListener('change', updateRetailerOptions);
    }
}

// Load dashboard data
async function loadDashboardData() {
    try {
        showLoading('Loading dashboard data...');
        
        console.log('Starting to load dashboard data...');
        
        // Load all service statuses in parallel with better error handling
        const statusPromises = [
            fetchAPI('/api/v1/bls/health').catch(e => ({ status: 'rejected', reason: e })),
            fetchAPI('/api/v1/storage/stats').catch(e => ({ status: 'rejected', reason: e })),
            fetchAPI('/api/v1/scrapers/health').catch(e => ({ status: 'rejected', reason: e })),
            fetchAPI('/api/v1/processing/health').catch(e => ({ status: 'rejected', reason: e }))
        ];
        
        const [blsStatus, storageStatus, scrapersStatus, processingStatus] = await Promise.allSettled(statusPromises);
        
        console.log('API responses:', { blsStatus, storageStatus, scrapersStatus, processingStatus });
        
        // Update status cards
        updateStatusCard('bls-status', blsStatus);
        updateStatusCard('storage-status', storageStatus);
        updateStatusCard('scrapers-status', scrapersStatus);
        updateStatusCard('processing-status', processingStatus);
        
        updateActivity('Dashboard data loaded successfully', 'success');
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        updateActivity('Error loading dashboard data: ' + error.message, 'error');
        
        // Set fallback status for all cards
        setFallbackStatus();
    } finally {
        hideLoading();
    }
}

// Set fallback status when API calls fail
function setFallbackStatus() {
    document.getElementById('bls-status').textContent = 'Unknown';
    document.getElementById('storage-status').textContent = 'Unknown';
    document.getElementById('scrapers-status').textContent = 'Unknown';
    document.getElementById('processing-status').textContent = 'Unknown';
}

// Load section-specific data
async function loadSectionData(section) {
    switch (section) {
        case 'compare':
            await loadCompareData();
            break;
        case 'scrape':
            await loadScrapeData();
            break;
        case 'api':
            await loadAPIData();
            break;
    }
}

// Load comparison section data
async function loadCompareData() {
    try {
        // Load available categories and retailers
        const [categoriesResponse, retailersResponse] = await Promise.allSettled([
            fetchAPI('/api/v1/scrapers/categories'),
            fetchAPI('/api/v1/scrapers/retailers')
        ]);
        
        if (categoriesResponse.status === 'fulfilled') {
            updateCategoryOptions(categoriesResponse.value.categories);
        }
        
        if (retailersResponse.status === 'fulfilled') {
            updateRetailerCheckboxes(retailersResponse.value.available_retailers);
        }
        
    } catch (error) {
        console.error('Error loading compare data:', error);
    }
}

// Load scraping section data
async function loadScrapeData() {
    try {
        const response = await fetchAPI('/api/v1/scrapers/categories');
        if (response.categories) {
            updateScrapeCategories(response.categories);
        }
    } catch (error) {
        console.error('Error loading scrape data:', error);
    }
}

// Load API section data
async function loadAPIData() {
    // API data is static, no need to load
    console.log('API section loaded');
}

// Update status card
function updateStatusCard(elementId, statusResult) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.warn(`Element not found: ${elementId}`);
        return;
    }
    
    console.log(`Updating status card ${elementId}:`, statusResult);
    
    if (statusResult.status === 'fulfilled') {
        const data = statusResult.value;
        
        // Handle case where data itself might be an error response
        if (data && data.status === 'rejected') {
            element.textContent = 'Error';
            console.error(`API error for ${elementId}:`, data.reason);
            return;
        }
        
        switch (elementId) {
            case 'bls-status':
                if (data && data.status) {
                    element.textContent = data.status === 'healthy' ? 'Healthy' : 'Error';
                } else {
                    element.textContent = 'Ready';
                }
                break;
            case 'storage-status':
                if (data && typeof data.total_series === 'number') {
                    element.textContent = `${data.total_series} Series`;
                } else {
                    element.textContent = 'Ready';
                }
                break;
            case 'scrapers-status':
                if (data && data.healthy_scrapers && data.total_scrapers) {
                    element.textContent = `${data.healthy_scrapers}/${data.total_scrapers}`;
                } else if (data && data.status === 'healthy') {
                    element.textContent = 'Ready';
                } else {
                    element.textContent = 'Ready';
                }
                break;
            case 'processing-status':
                if (data && data.status) {
                    element.textContent = data.status === 'healthy' ? 'Ready' : 'Error';
                } else {
                    element.textContent = 'Ready';
                }
                break;
            default:
                element.textContent = 'Ready';
        }
    } else {
        element.textContent = 'Error';
        console.error(`Status result error for ${elementId}:`, statusResult.reason);
    }
}

// Update category options
function updateCategoryOptions(categories) {
    const select = document.getElementById('category-select');
    if (!select || !categories) return;
    
    // Clear existing options except the first one
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    // Add category options
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category.charAt(0).toUpperCase() + category.slice(1).replace('_', ' ');
        select.appendChild(option);
    });
}

// Update retailer checkboxes
function updateRetailerCheckboxes(retailers) {
    const container = document.getElementById('retailer-checkboxes');
    if (!container || !retailers) return;
    
    container.innerHTML = '';
    
    retailers.forEach(retailer => {
        const label = document.createElement('label');
        label.className = 'checkbox-label';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = retailer;
        checkbox.checked = true;
        
        const checkmark = document.createElement('span');
        checkmark.className = 'checkmark';
        
        const text = document.createTextNode(retailer.charAt(0).toUpperCase() + retailer.slice(1));
        
        label.appendChild(checkbox);
        label.appendChild(checkmark);
        label.appendChild(text);
        
        container.appendChild(label);
    });
}

// Update scrape categories
function updateScrapeCategories(categories) {
    const select = document.getElementById('scrape-category');
    if (!select || !categories) return;
    
    // Clear existing options except the first one
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    // Add category options
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category.charAt(0).toUpperCase() + category.slice(1).replace('_', ' ');
        select.appendChild(option);
    });
}

// Quick action functions
async function quickScrape(category) {
    try {
        showLoading('Scraping ' + category + ' prices...');
        
        const response = await fetchAPI(`/api/v1/scrapers/demo/${category}`);
        
        if (response.success) {
            showToast(`Successfully scraped ${category} prices!`, 'success');
            updateActivity(`Scraped ${category} prices from ${Object.keys(response.results).length} retailers`, 'success');
        } else {
            showToast('Scraping failed', 'error');
        }
        
    } catch (error) {
        console.error('Quick scrape error:', error);
        showToast('Scraping error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function quickBLS(seriesId) {
    try {
        showLoading('Fetching BLS data...');
        
        const response = await fetchAPI(`/api/v1/bls/series/${seriesId}/info`);
        
        if (response.series_id) {
            showToast(`Loaded BLS series: ${response.title}`, 'success');
            updateActivity(`Fetched BLS data for ${seriesId}`, 'success');
        } else {
            showToast('Failed to load BLS data', 'error');
        }
        
    } catch (error) {
        console.error('Quick BLS error:', error);
        showToast('BLS error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function showComparison() {
    // Switch to compare section
    document.querySelector('.nav-link[data-section="compare"]').click();
}

function viewAPI() {
    // Switch to API section
    document.querySelector('.nav-link[data-section="api"]').click();
}

// Comparison functions
async function runComparison() {
    const category = document.getElementById('category-select').value;
    const zipCode = document.getElementById('zip-code').value;
    
    if (!category) {
        showToast('Please select a category', 'warning');
        return;
    }
    
    try {
        showLoading('Running price comparison...');
        
        // Get selected retailers
        const selectedRetailers = Array.from(document.querySelectorAll('#retailer-checkboxes input:checked'))
            .map(cb => cb.value);
        
        if (selectedRetailers.length === 0) {
            showToast('Please select at least one retailer', 'warning');
            return;
        }
        
        // Scrape retailer data
        const scrapeResponse = await fetchAPI('/api/v1/scrapers/category', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                category: category,
                retailers: selectedRetailers,
                max_results_per_retailer: 10,
                zip_code: zipCode,
                store_results: true
            })
        });
        
        if (scrapeResponse.success) {
            displayComparisonResults(scrapeResponse, category);
            updateActivity(`Compared ${category} prices across ${scrapeResponse.retailers_scraped} retailers`, 'success');
        } else {
            showToast('Comparison failed', 'error');
        }
        
    } catch (error) {
        console.error('Comparison error:', error);
        showToast('Comparison error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Display comparison results
function displayComparisonResults(data, category) {
    const resultsContainer = document.getElementById('comparison-results');
    const metaElement = document.getElementById('results-meta');
    const tableBody = document.getElementById('results-tbody');
    
    // Show results container
    resultsContainer.style.display = 'block';
    
    // Update meta information
    metaElement.textContent = `Found ${data.total_products_found} products across ${data.retailers_scraped} retailers`;
    
    // Clear and populate results table
    tableBody.innerHTML = '';
    
    const allProducts = [];
    
    // Collect all products from all retailers
    Object.entries(data.results_by_retailer).forEach(([retailer, result]) => {
        if (result.success && result.products) {
            result.products.forEach(product => {
                allProducts.push({
                    retailer: retailer,
                    ...product
                });
            });
        }
    });
    
    // Sort products by price
    allProducts.sort((a, b) => a.price - b.price);
    
    // Populate table
    allProducts.forEach(product => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td><strong>${product.retailer}</strong></td>
            <td>${product.name}</td>
            <td>$${product.price.toFixed(2)}</td>
            <td>${product.size || 'N/A'} ${product.unit || ''}</td>
            <td>${product.normalized_price ? '$' + product.normalized_price.toFixed(2) : 'N/A'}</td>
            <td><span class="comparison-badge">Pending</span></td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Create price chart
    createPriceChart(allProducts, category);
}

// Create price comparison chart
function createPriceChart(products, category) {
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    // Destroy existing chart
    if (currentChart) {
        currentChart.destroy();
    }
    
    // Group products by retailer
    const retailerData = {};
    products.forEach(product => {
        if (!retailerData[product.retailer]) {
            retailerData[product.retailer] = [];
        }
        retailerData[product.retailer].push(product.price);
    });
    
    // Calculate average prices per retailer
    const labels = Object.keys(retailerData);
    const avgPrices = labels.map(retailer => {
        const prices = retailerData[retailer];
        return prices.reduce((sum, price) => sum + price, 0) / prices.length;
    });
    
    currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `Average ${category} Price`,
                data: avgPrices,
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(72, 187, 120, 0.8)',
                    'rgba(237, 137, 54, 0.8)',
                    'rgba(159, 122, 234, 0.8)'
                ],
                borderColor: [
                    'rgba(102, 126, 234, 1)',
                    'rgba(72, 187, 120, 1)',
                    'rgba(237, 137, 54, 1)',
                    'rgba(159, 122, 234, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${category.charAt(0).toUpperCase() + category.slice(1)} Price Comparison`
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

// Scraping functions
async function startScraping() {
    const query = document.getElementById('scrape-query').value.trim();
    const category = document.getElementById('scrape-category').value;
    const maxResults = parseInt(document.getElementById('max-results').value);
    
    if (!query) {
        showToast('Please enter a search query', 'warning');
        return;
    }
    
    try {
        showScrapingStatus('Initializing scraping...');
        
        const requestBody = {
            query: query,
            max_results_per_retailer: maxResults,
            store_results: true
        };
        
        if (category) {
            requestBody.category = category;
        }
        
        const response = await fetchAPI('/api/v1/scrapers/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        hideScrapingStatus();
        
        if (response.success) {
            displayScrapingResults(response);
            updateActivity(`Scraped ${response.total_products_found} products for "${query}"`, 'success');
        } else {
            showToast('Scraping failed', 'error');
        }
        
    } catch (error) {
        console.error('Scraping error:', error);
        hideScrapingStatus();
        showToast('Scraping error: ' + error.message, 'error');
    }
}

async function scrapeMilkDemo() {
    try {
        showScrapingStatus('Running milk price demo...');
        
        const response = await fetchAPI('/api/v1/scrapers/demo/milk?max_results=5');
        
        hideScrapingStatus();
        
        if (response.success) {
            displayDemoResults(response);
            updateActivity('Completed milk price demo', 'success');
        } else {
            showToast('Demo failed', 'error');
        }
        
    } catch (error) {
        console.error('Demo error:', error);
        hideScrapingStatus();
        showToast('Demo error: ' + error.message, 'error');
    }
}

// Display scraping results
function displayScrapingResults(data) {
    const resultsContainer = document.getElementById('scraping-results');
    const metaElement = document.getElementById('scraping-meta');
    const productsContainer = document.getElementById('scraped-products');
    
    // Show results container
    resultsContainer.style.display = 'block';
    
    // Update meta information
    metaElement.textContent = `Found ${data.total_products_found} products in ${data.processing_time_seconds.toFixed(2)}s`;
    
    // Clear and populate products
    productsContainer.innerHTML = '';
    
    Object.entries(data.results_by_retailer).forEach(([retailer, result]) => {
        if (result.success && result.products) {
            result.products.forEach(product => {
                const productCard = createProductCard(retailer, product);
                productsContainer.appendChild(productCard);
            });
        }
    });
}

// Display demo results
function displayDemoResults(data) {
    const resultsContainer = document.getElementById('scraping-results');
    const metaElement = document.getElementById('scraping-meta');
    const productsContainer = document.getElementById('scraped-products');
    
    // Show results container
    resultsContainer.style.display = 'block';
    
    // Update meta information
    metaElement.textContent = `Demo completed for ZIP: ${data.zip_code}`;
    
    // Clear and populate products
    productsContainer.innerHTML = '';
    
    Object.entries(data.results).forEach(([retailer, result]) => {
        if (result.sample_products) {
            result.sample_products.forEach(product => {
                const productCard = createProductCard(retailer, product);
                productsContainer.appendChild(productCard);
            });
        }
    });
}

// Create product card element
function createProductCard(retailer, product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    
    const price = typeof product.price === 'string' ? product.price : `$${product.price.toFixed(2)}`;
    
    card.innerHTML = `
        <div class="product-name">${product.name}</div>
        <div class="product-price">${price}</div>
        <div class="product-details">
            <div><strong>Retailer:</strong> ${retailer}</div>
            ${product.brand ? `<div><strong>Brand:</strong> ${product.brand}</div>` : ''}
            ${product.size ? `<div><strong>Size:</strong> ${product.size} ${product.unit || ''}</div>` : ''}
            ${product.on_sale ? '<div class="sale-badge">On Sale!</div>' : ''}
        </div>
    `;
    
    return card;
}

// Show/hide scraping status
function showScrapingStatus(message) {
    const statusContainer = document.getElementById('scraping-status');
    const detailsElement = document.getElementById('scraping-details');
    
    statusContainer.style.display = 'block';
    detailsElement.textContent = message;
}

function hideScrapingStatus() {
    const statusContainer = document.getElementById('scraping-status');
    statusContainer.style.display = 'none';
}

// API testing functions
async function testEndpoint(endpoint) {
    try {
        showLoading(`Testing ${endpoint}...`);
        
        const response = await fetch(apiBaseUrl + endpoint);
        const data = await response.json();
        
        displayAPIResponse(endpoint, response.status, data);
        
    } catch (error) {
        console.error('API test error:', error);
        displayAPIResponse(endpoint, 'Error', { error: error.message });
    } finally {
        hideLoading();
    }
}

// Display API response
function displayAPIResponse(endpoint, status, data) {
    const responseContainer = document.getElementById('api-response');
    const headerElement = document.getElementById('response-header');
    const bodyElement = document.getElementById('response-body');
    
    // Show response container
    responseContainer.style.display = 'block';
    
    // Update header
    headerElement.textContent = `${endpoint} - Status: ${status}`;
    
    // Update body
    bodyElement.textContent = JSON.stringify(data, null, 2);
    
    // Scroll to response
    responseContainer.scrollIntoView({ behavior: 'smooth' });
}

// Utility functions
async function fetchAPI(endpoint, options = {}) {
    const url = apiBaseUrl + endpoint;
    
    console.log(`Fetching: ${url}`);
    
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        console.log(`Response for ${endpoint}:`, response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`API Error for ${endpoint}:`, errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log(`Data for ${endpoint}:`, data);
        return data;
        
    } catch (error) {
        console.error(`Fetch error for ${endpoint}:`, error);
        throw error;
    }
}

function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    const text = overlay.querySelector('.loading-text');
    
    text.textContent = message;
    overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = 'none';
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

function updateActivity(message, type = 'info') {
    const activityList = document.getElementById('activity-list');
    
    const activityItem = document.createElement('div');
    activityItem.className = 'activity-item';
    
    const iconClass = type === 'success' ? 'fa-check-circle' : 
                     type === 'error' ? 'fa-exclamation-circle' : 
                     type === 'warning' ? 'fa-exclamation-triangle' : 
                     'fa-info-circle';
    
    activityItem.innerHTML = `
        <div class="activity-icon">
            <i class="fas ${iconClass}"></i>
        </div>
        <div class="activity-content">
            <div class="activity-title">${message}</div>
            <div class="activity-time">${new Date().toLocaleTimeString()}</div>
        </div>
    `;
    
    // Add to top of list
    activityList.insertBefore(activityItem, activityList.firstChild);
    
    // Keep only last 10 activities
    while (activityList.children.length > 10) {
        activityList.removeChild(activityList.lastChild);
    }
}

// Update retailer options based on category
function updateRetailerOptions() {
    // This could be enhanced to show/hide retailers based on category support
    console.log('Category changed, updating retailer options...');
}
