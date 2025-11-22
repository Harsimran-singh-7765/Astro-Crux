// Constellation animation for Astro Crux
// All 12 Zodiac constellations with authentic star patterns

let canvas = null;
let ctx = null;

// Resize canvas to match container
function resizeCanvas() {
    if (!canvas) return;
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    console.log(`[Constellation] Canvas resized to ${canvas.width}x${canvas.height}`);
}

// Initialize canvas when available
function initCanvas() {
    canvas = document.getElementById('constellationCanvas');
    if (!canvas) {
        console.error("[Constellation] ❌ Canvas element not found!");
        return false;
    }
    
    ctx = canvas.getContext('2d');
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    console.log("[Constellation] ✅ Canvas initialized");
    return true;
}

// Constellation data (simplified versions of real zodiac constellations)
const constellations = [
    {
        name: 'Aries',
        stars: [[0, 0], [40, -20], [80, -10], [100, 20], [60, 30]],
        connections: [[0, 1], [1, 2], [2, 3], [2, 4]]
    },
    {
        name: 'Taurus',
        stars: [[0, 0], [50, -30], [90, -20], [60, 30], [20, 40], [100, 10], [80, 50]],
        connections: [[0, 1], [1, 2], [0, 3], [3, 4], [2, 5], [5, 6]]
    },
    {
        name: 'Gemini',
        stars: [[0, 0], [0, 80], [30, 20], [30, 100], [60, 40], [60, 120]],
        connections: [[0, 2], [2, 4], [1, 3], [3, 5], [0, 1], [4, 5], [2, 3]]
    },
    {
        name: 'Cancer',
        stars: [[0, 0], [40, 20], [80, 0], [60, 40], [40, 60], [20, 50]],
        connections: [[0, 1], [1, 2], [1, 3], [3, 4], [4, 5], [5, 0]]
    },
    {
        name: 'Leo',
        stars: [[0, 40], [40, 0], [80, 20], [100, 50], [70, 70], [30, 60], [50, 40]],
        connections: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [1, 6], [6, 4]]
    },
    {
        name: 'Virgo',
        stars: [[0, 0], [30, 40], [60, 60], [90, 50], [100, 20], [70, 0], [40, 30]],
        connections: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 1], [1, 6]]
    },
    {
        name: 'Libra',
        stars: [[0, 30], [40, 0], [80, 0], [120, 30], [80, 60], [40, 60], [50, 30]],
        connections: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [1, 6], [6, 4]]
    },
    {
        name: 'Scorpio',
        stars: [[0, 20], [30, 0], [60, 0], [90, 20], [110, 50], [100, 80], [70, 100], [30, 80]],
        connections: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 0]]
    },
    {
        name: 'Sagittarius',
        stars: [[0, 60], [40, 40], [70, 20], [100, 0], [60, 60], [40, 80], [20, 100]],
        connections: [[0, 1], [1, 2], [2, 3], [1, 4], [4, 5], [5, 6], [6, 4]]
    },
    {
        name: 'Capricorn',
        stars: [[0, 30], [40, 0], [80, 10], [100, 40], [70, 60], [30, 50], [50, 25]],
        connections: [[0, 1], [1, 2], [2, 3], [2, 4], [4, 5], [5, 0], [1, 6], [6, 4]]
    },
    {
        name: 'Aquarius',
        stars: [[0, 0], [40, 20], [80, 20], [120, 0], [40, 50], [80, 50], [20, 40], [100, 40]],
        connections: [[0, 1], [1, 2], [2, 3], [1, 4], [2, 5], [0, 6], [3, 7], [4, 5]]
    },
    {
        name: 'Pisces',
        stars: [[0, 40], [30, 20], [60, 0], [60, 80], [30, 60], [100, 40], [80, 0]],
        connections: [[0, 1], [1, 2], [3, 4], [4, 0], [2, 5], [5, 6]]
    }
];

// Create constellation instances with random positions and velocities
class ConstellationInstance {
    constructor(template, canvasWidth, canvasHeight) {
        this.template = template;
        this.x = Math.random() * canvasWidth;
        this.y = Math.random() * canvasHeight;
        this.vx = (Math.random() - 0.5) * 0.15; // Very slow drift
        this.vy = (Math.random() - 0.5) * 0.15;
        this.scale = 0.8 + Math.random() * 0.6;  // Smaller: 0.8-1.4
        this.opacity = 0.4 + Math.random() * 0.35; // 0.4-0.75
        this.rotation = Math.random() * Math.PI * 2;
        this.rotationSpeed = (Math.random() - 0.5) * 0.0005; // Slower rotation
        this.twinklePhase = Math.random() * Math.PI * 2; // For star twinkling
        this.pulsePhase = Math.random() * Math.PI * 2; // For glow pulsing
    }

    update(canvasWidth, canvasHeight) {
        this.x += this.vx;
        this.y += this.vy;
        this.rotation += this.rotationSpeed;
        this.twinklePhase += 0.05;
        this.pulsePhase += 0.02;

        // Wrap around screen with larger buffer
        if (this.x < -200) this.x = canvasWidth + 200;
        if (this.x > canvasWidth + 200) this.x = -200;
        if (this.y < -200) this.y = canvasHeight + 200;
        if (this.y > canvasHeight + 200) this.y = -200;
    }

    draw(ctx) {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.rotation);
        ctx.scale(this.scale, this.scale);
        ctx.globalAlpha = this.opacity;

        const color = 'rgba(212, 175, 55, 0.8)'; // Vedic gold - brighter
        const glowColor = 'rgba(212, 175, 55, 0.3)';
        
        // Draw connections (lines between stars) - thicker and brighter
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.beginPath();
        this.template.connections.forEach(([i, j]) => {
            const [x1, y1] = this.template.stars[i];
            const [x2, y2] = this.template.stars[j];
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
        });
        ctx.stroke();

        // Draw stars with twinkling effect
        const twinkleFactor = 0.7 + 0.3 * Math.sin(this.twinklePhase);
        const pulseFactor = 1 + 0.3 * Math.sin(this.pulsePhase);
        
        ctx.fillStyle = color;
        this.template.stars.forEach(([x, y], idx) => {
            // Main star with twinkling
            ctx.beginPath();
            const radius = (1.2 + idx * 0.15) * twinkleFactor; // Smaller varied star sizes
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fill();
            
            // Bright core
            ctx.beginPath();
            ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
            ctx.arc(x, y, radius * 0.4, 0, Math.PI * 2);
            ctx.fill();
            
            // Large glow with pulse
            ctx.beginPath();
            ctx.fillStyle = glowColor;
            ctx.arc(x, y, (3.5 + idx * 0.25) * pulseFactor, 0, Math.PI * 2);
            ctx.fill();
            
            // Medium glow layer
            ctx.beginPath();
            ctx.fillStyle = 'rgba(212, 175, 55, 0.15)';
            ctx.arc(x, y, (5 + idx * 0.4) * pulseFactor, 0, Math.PI * 2);
            ctx.fill();
            
            ctx.fillStyle = color;
        });

        // Draw constellation name - larger and more visible
        ctx.fillStyle = 'rgba(212, 175, 55, 0.6)';
        ctx.font = 'bold 14px serif';
        ctx.textAlign = 'center';
        const maxX = Math.max(...this.template.stars.map(s => s[0]));
        ctx.shadowColor = 'rgba(212, 175, 55, 0.3)';
        ctx.shadowBlur = 5;
        ctx.fillText(this.template.name, maxX / 2, -15);
        ctx.shadowColor = 'transparent';

        ctx.restore();
    }
}

// Create multiple instances of each constellation
const instances = [];
function initConstellations() {
    instances.length = 0;
    constellations.forEach(template => {
        // Create 2-3 instances of each constellation for richer background
        const count = 2 + Math.floor(Math.random() * 2);
        for (let i = 0; i < count; i++) {
            instances.push(new ConstellationInstance(template, canvas.width, canvas.height));
        }
    });
    console.log(`[Constellation] Created ${instances.length} constellation instances`);
}

// Animation loop
function animate() {
    if (!canvas || !ctx) return;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    instances.forEach(instance => {
        instance.update(canvas.width, canvas.height);
        instance.draw(ctx);
    });
    
    requestAnimationFrame(animate);
}

// Start animation when game panel is shown
function startConstellations() {
    console.log("[Constellation] 🌌 Starting constellations...");
    
    // Make sure canvas is initialized
    if (!initCanvas()) {
        console.error("[Constellation] ❌ Failed to initialize canvas");
        return;
    }
    
    canvas.classList.add('active');
    initConstellations();
    animate();
    
    console.log("[Constellation] ✅ Constellations started with " + instances.length + " instances");
}

// Initialize on load (but hidden)
function startInitialAnimation() {
    if (!initCanvas()) return;
    initConstellations();
    animate();
}

// Export for use in main script
window.startConstellations = startConstellations;
window.startInitialAnimation = startInitialAnimation;