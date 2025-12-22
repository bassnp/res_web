/**
 * PDF Thumbnail Generator Script
 * Generates a JPG thumbnail from the first page of a PDF file.
 * 
 * Usage: node public/generate_pdf_thumbnail.js [input.pdf] [output.jpg]
 * 
 * Dependencies: pdfjs-dist@4.x, canvas (installed via npm)
 */

const fs = require('fs');
const path = require('path');
const { createCanvas } = require('canvas');

// Node.js canvas factory for pdfjs-dist
class NodeCanvasFactory {
    create(width, height) {
        const canvas = createCanvas(width, height);
        const context = canvas.getContext('2d');
        return { canvas, context };
    }

    reset(canvasAndContext, width, height) {
        canvasAndContext.canvas.width = width;
        canvasAndContext.canvas.height = height;
    }

    destroy(canvasAndContext) {
        canvasAndContext.canvas.width = 0;
        canvasAndContext.canvas.height = 0;
        canvasAndContext.canvas = null;
        canvasAndContext.context = null;
    }
}

async function generateThumbnail(pdfPath, outputPath, scale = 1.5) {
    // Import pdfjs-dist v4.x
    const pdfjsLib = await import('pdfjs-dist/legacy/build/pdf.mjs');
    
    // Validate input file exists
    if (!fs.existsSync(pdfPath)) {
        console.error(`Error: PDF file not found: ${pdfPath}`);
        return false;
    }

    try {
        console.log(`Converting first page of: ${pdfPath}`);
        
        // Load PDF document
        const data = new Uint8Array(fs.readFileSync(pdfPath));
        
        // Set up loading task with canvas factory for Node.js
        const canvasFactory = new NodeCanvasFactory();
        const loadingTask = pdfjsLib.getDocument({ 
            data,
            standardFontDataUrl: 'https://unpkg.com/pdfjs-dist@4.4.168/standard_fonts/',
            canvasFactory: canvasFactory
        });
        const pdfDoc = await loadingTask.promise;
        
        if (pdfDoc.numPages === 0) {
            console.error('Error: PDF has no pages');
            return false;
        }

        // Get first page
        const page = await pdfDoc.getPage(1);
        const viewport = page.getViewport({ scale });

        // Create canvas
        const canvas = createCanvas(viewport.width, viewport.height);
        const context = canvas.getContext('2d');

        // Render page to canvas
        await page.render({
            canvasContext: context,
            viewport: viewport,
            canvasFactory: canvasFactory
        }).promise;

        // Ensure output directory exists
        const outputDir = path.dirname(outputPath);
        if (outputDir && !fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        // Save as JPEG
        const buffer = canvas.toBuffer('image/jpeg', { quality: 0.85 });
        fs.writeFileSync(outputPath, buffer);
        
        console.log(`Thumbnail saved to: ${outputPath}`);
        console.log(`Dimensions: ${canvas.width}x${canvas.height}`);
        
        return true;
    } catch (error) {
        console.error(`Error generating thumbnail: ${error.message}`);
        return false;
    }
}

async function main() {
    const publicDir = __dirname;
    
    // Default paths
    let pdfPath = path.join(publicDir, 'resources', 'resume.pdf');
    let outputPath = path.join(publicDir, 'resources', 'resume_thumb.jpg');
    
    // Allow command line overrides
    if (process.argv[2]) pdfPath = process.argv[2];
    if (process.argv[3]) outputPath = process.argv[3];
    
    console.log('='.repeat(50));
    console.log('PDF Thumbnail Generator');
    console.log('='.repeat(50));
    console.log(`Input PDF:  ${pdfPath}`);
    console.log(`Output JPG: ${outputPath}`);
    console.log('='.repeat(50));
    
    const success = await generateThumbnail(pdfPath, outputPath);
    
    if (success) {
        console.log('\nSuccess! Thumbnail generated.');
        process.exit(0);
    } else {
        console.log('\nFailed to generate thumbnail.');
        process.exit(1);
    }
}

main();
