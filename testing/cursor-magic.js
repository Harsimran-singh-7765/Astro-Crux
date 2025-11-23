/**
 * Mystical Cursor Effect
 * Adds purple glow and starry trail to cursor movement
 */

class MysticalCursor {
    constructor() {
        this.x = 0;
        this.y = 0;
        this.prevX = 0;
        this.prevY = 0;
        this.particles = [];
        this.mouseDown = false;
        this.trailPoints = [];
        
        this.init();
    }

    init() {
        // Track mouse position
        document.addEventListener('mousemove', (e) => this.onMouseMove(e));
        document.addEventListener('mousedown', () => this.mouseDown = true);
        document.addEventListener('mouseup', () => this.mouseDown = false);
        
        // Hide default cursor
        document.body.style.cursor = 'none';
        
        // Create canvas for effects
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'cursor-magic-canvas';
        this.canvas.style.position = 'fixed';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '9999';
        document.body.appendChild(this.canvas);
        
        this.ctx = this.canvas.getContext('2d');
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Handle window resize
        window.addEventListener('resize', () => {
            this.canvas.width = window.innerWidth;
            this.canvas.height = window.innerHeight;
        });
        
        // Start animation loop
        this.animate();
    }

    onMouseMove(e) {
        this.prevX = this.x;
        this.prevY = this.y;
        this.x = e.clientX;
        this.y = e.clientY;
        
        // Add trail point
        this.trailPoints.push({
            x: this.x,
            y: this.y,
            life: 1
        });
        
        // Keep trail length manageable
        if (this.trailPoints.length > 15) {
            this.trailPoints.shift();
        }
    }

    animate() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw comet tail
        this.drawCometTail();
        
        // Draw cursor ball
        this.drawCursorBall();
        
        requestAnimationFrame(() => this.animate());
    }

    drawCometTail() {
        // Fade trail points
        for (let i = 0; i < this.trailPoints.length; i++) {
            const p = this.trailPoints[i];
            p.life -= 0.08;
            
            if (p.life <= 0) {
                this.trailPoints.splice(i, 1);
                i--;
                continue;
            }
            
            // Size decreases towards the back
            const sizeRatio = (i / this.trailPoints.length);
            const size = 8 * sizeRatio * p.life;
            
            // Draw tail glow
            const gradient = this.ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, size * 2);
            gradient.addColorStop(0, `hsla(270, 100%, 60%, ${p.life * 0.6})`);
            gradient.addColorStop(0.5, `hsla(280, 100%, 45%, ${p.life * 0.3})`);
            gradient.addColorStop(1, `hsla(290, 100%, 30%, 0)`);
            
            this.ctx.fillStyle = gradient;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, size * 2, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Tail core
            this.ctx.fillStyle = `hsla(270, 100%, 70%, ${p.life * 0.8})`;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, size * 0.7, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    drawCursorBall() {
        const size = 10;
        const glowSize = 35;
        
        this.ctx.save();
        
        // Outer magical aura (pulsing)
        const pulse = Math.sin(Date.now() * 0.005) * 0.5 + 0.5;
        const auraSize = glowSize + pulse * 10;
        
        const auraGradient = this.ctx.createRadialGradient(
            this.x, this.y, 0,
            this.x, this.y, auraSize
        );
        auraGradient.addColorStop(0, 'rgba(192, 132, 250, 0.5)');     // Purple
        auraGradient.addColorStop(0.5, 'rgba(168, 85, 247, 0.25)');   // Violet
        auraGradient.addColorStop(1, 'rgba(147, 51, 234, 0)');        // Transparent
        
        this.ctx.fillStyle = auraGradient;
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, auraSize, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Inner glow layer
        const innerGradient = this.ctx.createRadialGradient(
            this.x, this.y, 0,
            this.x, this.y, glowSize
        );
        innerGradient.addColorStop(0, 'rgba(216, 180, 254, 0.7)');    // Light purple
        innerGradient.addColorStop(0.6, 'rgba(192, 132, 250, 0.4)');  // Medium purple
        innerGradient.addColorStop(1, 'rgba(168, 85, 247, 0)');       // Fade out
        
        this.ctx.fillStyle = innerGradient;
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, glowSize, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Spherical ball - 3D effect
        this.drawSphericalBall(this.x, this.y, size);
        
        this.ctx.restore();
    }

    drawSphericalBall(x, y, size) {
        this.ctx.save();
        
        // Outer sphere shadow for depth
        const shadowGradient = this.ctx.createRadialGradient(x, y, 0, x, y, size * 1.1);
        shadowGradient.addColorStop(0, 'rgba(168, 85, 247, 0.3)');
        shadowGradient.addColorStop(1, 'rgba(100, 40, 200, 0.1)');
        
        this.ctx.fillStyle = shadowGradient;
        this.ctx.beginPath();
        this.ctx.arc(x, y, size * 1.1, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Main sphere with 3D gradient
        const sphereGradient = this.ctx.createRadialGradient(
            x - size * 0.3, y - size * 0.3, 0,
            x, y, size * 1.2
        );
        sphereGradient.addColorStop(0, 'rgba(230, 204, 255, 1)');      // Bright center
        sphereGradient.addColorStop(0.4, 'rgba(200, 140, 255, 0.9)');  // Mid tone
        sphereGradient.addColorStop(0.8, 'rgba(168, 85, 247, 0.8)');   // Purple
        sphereGradient.addColorStop(1, 'rgba(120, 40, 200, 0.6)');     // Dark edge
        
        this.ctx.fillStyle = sphereGradient;
        this.ctx.beginPath();
        this.ctx.arc(x, y, size, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Sphere outline with glow
        this.ctx.strokeStyle = 'rgba(216, 180, 254, 0.9)';
        this.ctx.lineWidth = 1.5;
        this.ctx.shadowColor = 'rgba(192, 132, 250, 0.9)';
        this.ctx.shadowBlur = 12;
        this.ctx.beginPath();
        this.ctx.arc(x, y, size, 0, Math.PI * 2);
        this.ctx.stroke();
        
        // Bright highlight for glossy effect
        const highlightGradient = this.ctx.createRadialGradient(
            x - size * 0.4, y - size * 0.4, 0,
            x - size * 0.4, y - size * 0.4, size * 0.6
        );
        highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.7)');
        highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
        
        this.ctx.fillStyle = highlightGradient;
        this.ctx.beginPath();
        this.ctx.arc(x - size * 0.4, y - size * 0.4, size * 0.6, 0, Math.PI * 2);
        this.ctx.fill();
        
        this.ctx.restore();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new MysticalCursor();
    });
} else {
    new MysticalCursor();
}
