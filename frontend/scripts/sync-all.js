/**
 * Sync All Resources Script
 * 
 * This script orchestrates all resource synchronization tasks:
 * 1. Collage images
 * 2. Timeline showcase images
 * 3. Project showcase images
 * 4. PDF thumbnail generation
 * 
 * Usage: node scripts/sync-all.js
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const SCRIPTS_DIR = path.join(__dirname, '..', 'public');

const scripts = [
    'sync_collage_images.js',
    'sync_timeline_images.js',
    'sync_project_images.js',
    'generate_pdf_thumbnail.js'
];

console.log('='.repeat(60));
console.log('STARTING RESOURCE SYNCHRONIZATION');
console.log('='.repeat(60));

let hasError = false;

scripts.forEach(script => {
    const scriptPath = path.join(SCRIPTS_DIR, script);
    
    if (!fs.existsSync(scriptPath)) {
        console.warn(`[SKIP] Script not found: ${script}`);
        return;
    }

    console.log(`\n[RUNNING] ${script}...`);
    try {
        // Run the script and inherit stdio to show output in real-time
        execSync(`node "${scriptPath}"`, { stdio: 'inherit' });
        console.log(`[SUCCESS] ${script} completed.`);
    } catch (error) {
        console.error(`[ERROR] ${script} failed:`, error.message);
        // We don't exit immediately to allow other scripts to run, 
        // but we mark that an error occurred.
        hasError = true;
    }
});

console.log('\n' + '='.repeat(60));
if (hasError) {
    console.error('RESOURCE SYNCHRONIZATION COMPLETED WITH ERRORS');
    console.log('='.repeat(60));
    process.exit(1);
} else {
    console.log('ALL RESOURCES SYNCHRONIZED SUCCESSFULLY');
    console.log('='.repeat(60));
    process.exit(0);
}
