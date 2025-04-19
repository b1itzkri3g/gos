// Initialize AOS (Animate on Scroll)
document.addEventListener('DOMContentLoaded', function() {
    AOS.init({
        duration: 1000,
        once: true
    });

    // Global Variables
    let currentProductId = null;
    
    // Fetch products (already loaded via Jinja template)
    // Use window.productsData which is set in the index.html template
    const productsData = window.productsData || [];
    
    if (!productsData || productsData.length === 0) {
        console.error('No products data available. Make sure it is properly set in the HTML template.');
    }
    
    // Filter Products
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active state
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Get filter type
            const filterType = this.getAttribute('data-filter');
            
            // Filter products
            let filteredProducts = filterType === 'all' 
                ? productsData 
                : productsData.filter(product => product.type.toLowerCase() === filterType.toLowerCase());
            
            // Get the products grid
            const grid = document.getElementById('productsGrid');
            
            // Clear the grid
            grid.innerHTML = '';
            
            // Add filtered products
            filteredProducts.forEach(product => {
                // Fix image path - ensure we don't have duplicated 'static'
                let imagePath = product.image || '';
                if (imagePath.startsWith('static/')) {
                    imagePath = imagePath.substring(7); // Remove 'static/' prefix
                }
                
                const col = document.createElement('div');
                col.className = 'col-md-6 col-lg-4 mb-4';
                col.setAttribute('data-aos', 'fade-up');
                
                col.innerHTML = `
                    <div class="strain-card">
                        <div class="strain-image-wrapper">
                            <img src="/static/${imagePath}" alt="${product.name}" class="strain-image" onerror="this.src='/static/images/products/default.jpg'">
                            <div class="strain-type-badge">${product.type}</div>
                            <div class="availability-badge ${product.status === 'Active' ? 'in_stock' : product.status === 'Low Stock' ? 'low_stock' : 'out_of_stock'}">
                                ${product.status === 'Active' ? 'In Stock' : product.status === 'Low Stock' ? 'Low Stock' : 'Out of Stock'}
                            </div>
                        </div>
                        <div class="strain-content">
                            <h3 class="strain-title">${product.name}</h3>
                            <div class="strain-meta">
                                <div class="strain-info">
                                    <i class="fas fa-flask"></i> ${product.thc}
                                </div>
                                <div class="strain-price">${product.price}</div>
                            </div>
                            <div class="strain-effects">
                                ${product.effects && product.effects.length > 0 ? product.effects.map(effect => `
                                    <span class="effect-pill"><i class="${effect.icon}"></i> ${effect.name}</span>
                                `).join('') : ''}
                            </div>
                            <button class="btn-buy-now mt-3" onclick="showProductDetails(${product.id})">
                                View Details
                            </button>
                        </div>
                    </div>
                `;
                
                grid.appendChild(col);
            });
        });
    });
    
    // Make showProductDetails globally accessible
    window.showProductDetails = function(productId) {
        try {
            // Get current productsData from window
            let productsData = window.productsData || [];
            
            // Find the product by ID
            let product = productsData.find(p => p.id == productId);
            
            // If product not found in window data, try to fetch it from the API
            if (!product) {
                console.log('Product not found in window data, fetching from API...');
                fetch(`/api/products/${productId}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Product not found');
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('Successfully fetched product data:', data);
                        populateProductDetails(data);
                    })
                    .catch(error => {
                        console.error('Error fetching product details:', error);
                        alert('Sorry, we could not load the product details. Please try again later.');
                    });
                return;
            }
            
            // If product was found in window data, populate details directly
            populateProductDetails(product);
        } catch (error) {
            console.error('Error in showProductDetails:', error);
        }
    };
    
    // Function to populate the product details modal
    function populateProductDetails(product) {
        try {
            // Set the title
            const titleEl = document.getElementById('strainDetailsTitle');
            if (titleEl) {
                titleEl.textContent = product.name;
            }
            
            // Fix image path - ensure we don't have duplicated 'static'
            let imagePath = product.image || '';
            if (imagePath.startsWith('static/')) {
                imagePath = imagePath.substring(7); // Remove 'static/' prefix
            }
            
            // Set image with fallback
            const imageEl = document.getElementById('strainDetailsImage');
            if (imageEl) {
                imageEl.src = `/static/${imagePath}`;
                imageEl.alt = product.name;
                imageEl.onerror = function() {
                    this.src = '/static/images/products/default.jpg';
                    console.log('Failed to load product image, using default');
                };
            }
            
            // Type information with proper icon
            const typeEl = document.getElementById('strainDetailsType');
            if (typeEl) {
                typeEl.textContent = product.type;
            }
            
            // Set type badge - Check if element exists before using it
            const typeBadge = document.getElementById('strainDetailsTypeBadge');
            if (typeBadge) {
                typeBadge.textContent = product.type;
                typeBadge.className = 'strain-detail-type';
            }
            
            // Set other details
            const thcEl = document.getElementById('strainDetailsTHC');
            if (thcEl) {
                thcEl.textContent = product.thc;
            }
            
            const priceEl = document.getElementById('strainDetailsPrice');
            if (priceEl) {
                priceEl.textContent = product.price;
            }
            
            // Set availability with proper styling
            const availabilityEl = document.getElementById('strainDetailsAvailability');
            if (availabilityEl) {
                let availabilityStatus = '';
                
                if (product.status === 'Active' || product.status === 'In Stock') {
                    availabilityStatus = 'In Stock';
                    availabilityEl.innerHTML = '<i class="fas fa-check-circle"></i> In Stock';
                } else if (product.status === 'Low Stock') {
                    availabilityStatus = 'Low Stock';
                    availabilityEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> Low Stock';
                } else {
                    availabilityStatus = 'Out of Stock';
                    availabilityEl.innerHTML = '<i class="fas fa-times-circle"></i> Out of Stock';
                }
                
                // Set the data-status attribute for CSS styling
                availabilityEl.setAttribute('data-status', availabilityStatus);
            }
            
            // Description with fallback for empty descriptions
            const descriptionEl = document.getElementById('strainDetailsDescription');
            if (descriptionEl) {
                if (product.description && product.description.trim() !== '') {
                    descriptionEl.textContent = product.description;
                } else {
                    descriptionEl.textContent = 'No description available for this product.';
                }
            }
            
            // Clear existing effects
            const effectsContainer = document.getElementById('strainDetailsEffects');
            if (effectsContainer) {
                effectsContainer.innerHTML = '';
                
                // Add effects with icons
                if (product.effects && product.effects.length > 0) {
                    product.effects.forEach(effect => {
                        const effectTag = document.createElement('div');
                        effectTag.className = 'effect-tag';
                        
                        // Use the effect's icon if available, otherwise use a default
                        const iconClass = effect.icon || 'fas fa-cannabis';
                        
                        effectTag.innerHTML = `<i class="${iconClass}"></i> ${effect.name}`;
                        effectsContainer.appendChild(effectTag);
                    });
                } else {
                    // If no effects are specified, add a default effect based on the product type
                    const defaultEffect = document.createElement('div');
                    defaultEffect.className = 'effect-tag';
                    
                    if (product.type === 'Sativa') {
                        defaultEffect.innerHTML = '<i class="fas fa-bolt"></i> Energetic';
                    } else if (product.type === 'Indica') {
                        defaultEffect.innerHTML = '<i class="fas fa-couch"></i> Relaxing';
                    } else {
                        defaultEffect.innerHTML = '<i class="fas fa-balance-scale"></i> Balanced';
                    }
                    
                    effectsContainer.appendChild(defaultEffect);
                }
            }
            
            // Set up the Buy Now button click handler
            const buyNowBtn = document.getElementById('buyNowButton');
            if (buyNowBtn) {
                buyNowBtn.onclick = () => {
                    // Try to find both modals
                    const strainModal = document.getElementById('strainDetailsModal');
                    const productModal = document.getElementById('productDetailsModal');
                    
                    // Determine which modal is active
                    const activeModal = strainModal || productModal;
                    
                    if (activeModal) {
                        let modalInstance = bootstrap.Modal.getInstance(activeModal);
                        if (!modalInstance) {
                            modalInstance = new bootstrap.Modal(activeModal);
                        }
                        modalInstance.hide();
                        
                        setTimeout(() => {
                            const checkoutModal = document.getElementById('checkoutModal');
                            if (checkoutModal) {
                                const checkoutInstance = new bootstrap.Modal(checkoutModal);
                                checkoutInstance.show();
                                populateCheckoutModal(product);
                            }
                        }, 300);
                    }
                };
            }
            
            // Show the modal - try to determine which one to use
            const strainModal = document.getElementById('strainDetailsModal');
            const productModal = document.getElementById('productDetailsModal');
            
            // Use whichever one exists
            if (strainModal) {
                const modalInstance = new bootstrap.Modal(strainModal);
                modalInstance.show();
            } else if (productModal) {
                const modalInstance = new bootstrap.Modal(productModal);
                modalInstance.show();
            }
        } catch (error) {
            console.error('Error in populateProductDetails:', error);
        }
    }
    
    // Make populateCheckoutModal accessible
    window.populateCheckoutModal = function(product) {
        try {
            // Fix image path - ensure we don't have duplicated 'static'
            let imagePath = product.image || '';
            if (imagePath.startsWith('static/')) {
                imagePath = imagePath.substring(7); // Remove 'static/' prefix
            }
            
            // Set product details in the checkout modal
            document.getElementById('checkoutTitle').textContent = product.name;
            document.getElementById('checkoutPrice').textContent = product.price;
            document.getElementById('checkoutType').textContent = product.type;
            
            // Set the product image with fallback
            const imageEl = document.getElementById('checkoutImage');
            imageEl.src = `/static/${imagePath}`;
            imageEl.alt = product.name;
            imageEl.onerror = function() {
                this.src = '/static/images/products/default.jpg';
                console.log('Failed to load product image in checkout, using default');
            };
        } catch (error) {
            console.error('Error in populateCheckoutModal:', error);
        }
    };

    // Contact Form Submission
    const contactForm = document.querySelector('.contact-form form');
    if(contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // In a real app, you would send the form data to the server here
            // For now, just show an alert
            alert('Thank you for your message! We will get back to you soon.');
            
            // Reset the form
            this.reset();
        });
    }
});