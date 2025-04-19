/**
 * Analytics Demo Data Generator
 *
 * This script generates dummy visit data for testing the analytics dashboard.
 * It simulates visits over the past 365 days with various patterns.
 */

// Function to add a specified number of days to a date
function addDays(date, days) {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

// Function to format date to ISO string
function formatDate(date) {
    return date.toISOString();
}

// Function to generate a random visitor ID
function generateVisitorId() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

// Pages to simulate visits for
const pages = [
    'home',
    'product_1',
    'product_2',
    'admin_dashboard',
    'admin_analytics',
    'admin_settings',
    'admin_giftboxes',
    'admin_login_page',
    'admin_login_success',
    'admin_login_failed',
    'api_products'
];

// Function to generate a random page
function getRandomPage() {
    return pages[Math.floor(Math.random() * pages.length)];
}

// Function to generate demo data
function generateDemoData(daysBack) {
    const visits = [];
    const today = new Date();
    
    // Number of visitors per day with some randomness
    const baseVisitorsPerDay = 20;
    
    // Generate visits for each day
    for (let i = daysBack; i >= 0; i--) {
        const visitDate = addDays(today, -i);
        
        // Add weekly pattern (more visits on weekends)
        let dailyVariation = 1;
        if (visitDate.getDay() === 0 || visitDate.getDay() === 6) {
            dailyVariation = 1.5; // 50% more visits on weekends
        }
        
        // Add monthly growth trend (gradual increase in visits)
        const monthFactor = 1 + (daysBack - i) / (daysBack * 3); // Gradual increase over time
        
        // Calculate number of visits for this day
        const visitorsToday = Math.floor(baseVisitorsPerDay * dailyVariation * monthFactor);
        
        // Create visitor pool for the day (some visitors visit multiple pages)
        const visitorPool = [];
        for (let v = 0; v < Math.ceil(visitorsToday * 0.7); v++) {
            visitorPool.push(generateVisitorId());
        }
        
        // Generate visits for this day
        for (let j = 0; j < visitorsToday; j++) {
            // Pick a visitor (with some repeat visitors)
            const visitorIndex = Math.min(Math.floor(Math.random() * visitorPool.length), visitorPool.length - 1);
            const visitorId = visitorPool[visitorIndex];
            
            // Set random time during the day
            const visitDateTime = new Date(visitDate);
            visitDateTime.setHours(Math.floor(Math.random() * 24));
            visitDateTime.setMinutes(Math.floor(Math.random() * 60));
            visitDateTime.setSeconds(Math.floor(Math.random() * 60));
            
            // Create visit record
            visits.push({
                timestamp: formatDate(visitDateTime),
                path: getRandomPage(),
                visitor_id: visitorId,
                referrer: 'demo'
            });
        }
    }
    
    return visits;
}

// Function to populate the visits.json file with demo data
function populateDemoData() {
    const data = generateDemoData(365); // Generate data for the past year
    
    // Log the data for debugging
    console.log('Generated demo data:', data.length, 'visits');
    
    // In a real application, you would send this data to the server
    // to save in the visits.json file
    
    // For now, we'll just store it in localStorage for demo purposes
    localStorage.setItem('demo_analytics_data', JSON.stringify(data));
    
    return data;
}

// Call the function to generate demo data when this script is loaded
populateDemoData(); 