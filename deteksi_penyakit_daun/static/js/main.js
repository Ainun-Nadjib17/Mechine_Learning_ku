// TomatAI - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {

    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Upload zone functionality
    const uploadZone = document.getElementById('uploadZone');
    const imageInput = document.getElementById('imageInput');
    const previewArea = document.getElementById('previewArea');
    const previewImage = document.getElementById('previewImage');
    const previewName = document.getElementById('previewName');
    const detectForm = document.getElementById('detectForm');
    const detectBtn = document.getElementById('detectBtn');
    const loadingArea = document.getElementById('loadingArea');

    if (uploadZone) {
        // Click to upload
        uploadZone.addEventListener('click', function() {
            imageInput.click();
        });

        // Drag and drop
        uploadZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', function() {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadZone.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                imageInput.files = files;
                showPreview(files[0]);
            }
        });

        // File input change
        imageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                showPreview(this.files[0]);
            }
        });
    }

    // Show image preview
    function showPreview(file) {
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewName.textContent = file.name;
                previewArea.style.display = 'block';
                uploadZone.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }
    }

    // Form submission with loading
    if (detectForm) {
        detectForm.addEventListener('submit', function() {
            detectBtn.disabled = true;
            detectBtn.innerHTML = '⏳ Memproses...';
            loadingArea.style.display = 'block';
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Animate confidence bars on results page
    const confidenceFills = document.querySelectorAll('.confidence-fill');
    confidenceFills.forEach(fill => {
        const width = fill.style.width;
        fill.style.width = '0%';
        setTimeout(() => {
            fill.style.width = width;
        }, 100);
    });

});
