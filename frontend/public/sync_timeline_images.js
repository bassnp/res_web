/**
 * Sync Timeline Showcase Images Script
 * Scans each showcase folder and generates a manifest.json per folder
 * with alphanumerically sorted image paths.
 * 
 * Usage: node public/sync_timeline_images.js
 * 
 * Run this after adding new images to public/resources/timeline_images/showcase{N}/
 */

const fs = require('fs');
const path = require('path');

const publicDir = __dirname;
const timelineDir = path.join(publicDir, 'resources', 'timeline_images');

// Supported image extensions
const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];

function syncShowcaseImages() {
    console.log('='.repeat(50));
    console.log('Timeline Showcase Image Sync');
    console.log('='.repeat(50));
    
    // Create timeline_images directory if it doesn't exist
    if (!fs.existsSync(timelineDir)) {
        fs.mkdirSync(timelineDir, { recursive: true });
        console.log(`Created directory: ${timelineDir}`);
    }
    
    // Find all showcase directories
    const showcaseDirs = fs.readdirSync(timelineDir)
        .filter(item => {
            const itemPath = path.join(timelineDir, item);
            return fs.statSync(itemPath).isDirectory() && item.startsWith('showcase');
        })
        .sort((a, b) => {
            const numA = parseInt(a.replace('showcase', '')) || 0;
            const numB = parseInt(b.replace('showcase', '')) || 0;
            return numA - numB;
        });
    
    if (showcaseDirs.length === 0) {
        console.log('\nNo showcase directories found.');
        console.log('Create folders like: timeline_images/showcase1/, showcase2/, etc.');
        console.log('='.repeat(50));
        return;
    }
    
    console.log(`\nFound ${showcaseDirs.length} showcase folder(s):\n`);
    
    // Process each showcase directory
    showcaseDirs.forEach(showcaseDir => {
        const showcasePath = path.join(timelineDir, showcaseDir);
        const manifestPath = path.join(showcasePath, 'manifest.json');
        
        // Get all image files, sorted alphanumerically
        const files = fs.readdirSync(showcasePath)
            .filter(file => {
                const ext = path.extname(file).toLowerCase();
                return IMAGE_EXTENSIONS.includes(ext);
            })
            .sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }));
        
        console.log(`  ${showcaseDir}/`);
        
        // Build image paths array
        const imagePaths = files.map(file => {
            console.log(`    - ${file}`);
            return `/resources/timeline_images/${showcaseDir}/${file}`;
        });
        
        if (files.length === 0) {
            console.log('    (no images)');
        }
        
        // Generate manifest JSON
        const manifest = {
            images: imagePaths
        };
        
        fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
        console.log(`    -> manifest.json (${files.length} images)\n`);
    });
    
    console.log('='.repeat(50));
    console.log('Timeline sync complete!');
    console.log('='.repeat(50));
}

syncShowcaseImages();
