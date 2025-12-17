/**
 * Sync Project Showcase Images Script
 * Scans each project folder and generates a manifest.json per folder
 * with alphanumerically sorted image paths.
 * 
 * Usage: node public/sync_project_images.js
 * 
 * Run this after adding new images to public/resources/project_images/{project_folder}/
 * 
 * Expected folder structure:
 *   public/resources/project_images/
 *     ├── project-alpha/
 *     │   ├── 1.jpg
 *     │   ├── 2.png
 *     │   └── manifest.json (auto-generated)
 *     ├── project-beta/
 *     │   └── ...
 *     └── project-gamma/
 *         └── ...
 */

const fs = require('fs');
const path = require('path');

const publicDir = __dirname;
const projectsDir = path.join(publicDir, 'resources', 'project_images');

// Supported image extensions
const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];

/**
 * Synchronizes project images by scanning folders and generating manifests.
 * Creates the project_images directory if it doesn't exist.
 */
function syncProjectImages() {
    console.log('='.repeat(50));
    console.log('Project Showcase Image Sync');
    console.log('='.repeat(50));
    
    // Create project_images directory if it doesn't exist
    if (!fs.existsSync(projectsDir)) {
        fs.mkdirSync(projectsDir, { recursive: true });
        console.log(`Created directory: ${projectsDir}`);
    }
    
    // Find all project directories
    const projectDirs = fs.readdirSync(projectsDir)
        .filter(item => {
            const itemPath = path.join(projectsDir, item);
            return fs.statSync(itemPath).isDirectory();
        })
        .sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
    
    if (projectDirs.length === 0) {
        console.log('\nNo project directories found.');
        console.log('Create folders like: project_images/project-alpha/, project-beta/, etc.');
        console.log('Use kebab-case folder names matching your project IDs.');
        console.log('='.repeat(50));
        return;
    }
    
    console.log(`\nFound ${projectDirs.length} project folder(s):\n`);
    
    // Process each project directory
    projectDirs.forEach(projectDir => {
        const projectPath = path.join(projectsDir, projectDir);
        const manifestPath = path.join(projectPath, 'manifest.json');
        
        // Get all image files, sorted alphanumerically
        const files = fs.readdirSync(projectPath)
            .filter(file => {
                const ext = path.extname(file).toLowerCase();
                return IMAGE_EXTENSIONS.includes(ext);
            })
            .sort((a, b) => a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }));
        
        console.log(`  ${projectDir}/`);
        
        // Build image paths array
        const imagePaths = files.map(file => {
            console.log(`    - ${file}`);
            return `/resources/project_images/${projectDir}/${file}`;
        });
        
        if (files.length === 0) {
            console.log('    (no images)');
        }
        
        // Generate manifest JSON
        const manifest = {
            generated: new Date().toISOString(),
            projectId: projectDir,
            count: imagePaths.length,
            images: imagePaths
        };
        
        fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
        console.log(`    -> manifest.json (${files.length} images)\n`);
    });
    
    console.log('='.repeat(50));
    console.log('Project image sync complete!');
    console.log('='.repeat(50));
}

syncProjectImages();
