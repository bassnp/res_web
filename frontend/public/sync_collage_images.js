/**
 * Sync Collage Images Script
 * Scans the personal_collage folder and generates a manifest.json
 * with alphanumerically sorted image paths.
 * 
 * Usage: node public/sync_collage_images.js
 * 
 * Run this after adding new images to public/resources/personal_collage/
 */

const fs = require('fs');
const path = require('path');

const publicDir = __dirname;
const collageDir = path.join(publicDir, 'resources', 'personal_collage');
const manifestPath = path.join(publicDir, 'resources', 'collage_manifest.json');

// Supported image extensions
const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];

function syncImages() {
    console.log('='.repeat(50));
    console.log('Collage Image Sync');
    console.log('='.repeat(50));
    
    // Validate collage directory exists
    if (!fs.existsSync(collageDir)) {
        console.error(`Error: Collage directory not found: ${collageDir}`);
        process.exit(1);
    }
    
    // Get all image files, sorted alphanumerically
    const files = fs.readdirSync(collageDir)
        .filter(file => {
            const ext = path.extname(file).toLowerCase();
            return IMAGE_EXTENSIONS.includes(ext);
        })
        .sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }));
    
    console.log(`\nFound ${files.length} images:`);
    
    // Build image paths array
    const imagePaths = files.map((file, index) => {
        console.log(`  ${index + 1}. ${file}`);
        return `/resources/personal_collage/${file}`;
    });
    
    // Generate manifest JSON
    const manifest = {
        generated: new Date().toISOString(),
        count: imagePaths.length,
        images: imagePaths
    };
    
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
    
    console.log(`\nManifest saved to: ${manifestPath}`);
    console.log('='.repeat(50));
    console.log('Sync complete!');
    console.log('='.repeat(50));
}

syncImages();
