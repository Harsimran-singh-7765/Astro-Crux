/**
 * Mystical Cursor Effect
 * Adds purple glow and starry trail to cursor movement
 */

class MysticalCursor {
    constructor() {
        this.x = 0;
        this.y = 0;
        this.particles = [];
        this.mouseDown = false;
        
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
        this.x = e.clientX;
        this.y = e.clientY;
        
        // Create star particles
        this.createStars();
    }

    createStars() {
        // Add multiple stars per movement
        for (let i = 0; i < 3; i++) {
            const angle = Math.random() * Math.PI * 2;
            const velocity = 1 + Math.random() * 2;
            
            this.particles.push({
                x: this.x,
                y: this.y,
                vx: Math.cos(angle) * velocity,
                vy: Math.sin(angle) * velocity,
                life: 1,
                size: Math.random() * 2 + 1,
                hue: 260 + Math.random() * 30, // Purple to violet range
                opacity: 1
            });
        }
    }

    animate() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update and draw particles
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            
            // Update position
            p.x += p.vx;
            p.y += p.vy;
            
            // Fade out
            p.life -= 0.02;
            p.opacity = p.life;
            
            // Add gravity effect
            p.vy += 0.1;
            
            // Draw star
            this.drawStar(p);
            
            // Remove dead particles
            if (p.life <= 0) {
                this.particles.splice(i, 1);
            }
        }
        
        // Draw cursor glow and core
        this.drawCursor();
        
        requestAnimationFrame(() => this.animate());
    }

    drawStar(p) {
        this.ctx.save();
        this.ctx.globalAlpha = p.opacity;
        
        // Star glow
        const gradient = this.ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 3);
        gradient.addColorStop(0, `hsla(${p.hue}, 100%, 60%, ${p.opacity})`);
        gradient.addColorStop(0.5, `hsla(${p.hue}, 100%, 40%, ${p.opacity * 0.5})`);
        gradient.addColorStop(1, `hsla(${p.hue}, 100%, 20%, 0)`);
        
        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.size * 3, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Star core
        this.ctx.fillStyle = `hsla(${p.hue}, 100%, 80%, ${p.opacity})`;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        this.ctx.fill();
        
        this.ctx.restore();
    }

    drawCursor() {
        const size = 12;
        const glowSize = 30;
        
        this.ctx.save();
        
        // Outer magical aura (pulsing)
        const pulse = Math.sin(Date.now() * 0.005) * 0.5 + 0.5;
        const auraSize = glowSize + pulse * 10;
        
        const auraGradient = this.ctx.createRadialGradient(
            this.x, this.y, 0,
            this.x, this.y, auraSize
        );
        auraGradient.addColorStop(0, 'rgba(168, 85, 247, 0.4)');      // Purple
        auraGradient.addColorStop(0.5, 'rgba(147, 51, 234, 0.2)');    // Violet
        auraGradient.addColorStop(1, 'rgba(139, 92, 246, 0)');        // Transparent
        
        this.ctx.fillStyle = auraGradient;
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, auraSize, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Inner glow
        const innerGradient = this.ctx.createRadialGradient(
            this.x, this.y, 0,
            this.x, this.y, glowSize
        );
        innerGradient.addColorStop(0, 'rgba(196, 181, 253, 0.8)');    // Light purple
        innerGradient.addColorStop(0.6, 'rgba(168, 85, 247, 0.4)');   // Medium purple
        innerGradient.addColorStop(1, 'rgba(147, 51, 234, 0)');       // Fade out
        
        this.ctx.fillStyle = innerGradient;
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, glowSize, 0, Math.PI * 2);
        this.ctx.fill();
        
        // Cursor center - mystical star
        this.drawMysticalStar(this.x, this.y, size);
        
        this.ctx.restore();
    }

    drawMysticalStar(x, y, size) {
        this.ctx.save();
        
        // Star outline glow
        this.ctx.strokeStyle = 'rgba(196, 181, 253, 0.8)';
        this.ctx.lineWidth = 2;
        this.ctx.shadowColor = 'rgba(168, 85, 247, 0.8)';
        this.ctx.shadowBlur = 15;
        
        // Draw 5-pointed star
        this.ctx.beginPath();
        for (let i = 0; i < 5; i++) {
            const angle = (i * 4 * Math.PI) / 5 - Math.PI / 2;
            const sx = x + Math.cos(angle) * size;
            const sy = y + Math.sin(angle) * size;
            
            if (i === 0) this.ctx.moveTo(sx, sy);
            else this.ctx.lineTo(sx, sy);
        }
        this.ctx.closePath();
        this.ctx.stroke();
        
        // Star fill with gradient
        const starGradient = this.ctx.createRadialGradient(x, y, 0, x, y, size);
        starGradient.addColorStop(0, 'rgba(220, 198, 255, 1)');       // White-purple center
        starGradient.addColorStop(1, 'rgba(168, 85, 247, 0.6)');      // Purple edge
        
        this.ctx.fillStyle = starGradient;
        this.ctx.fill();
        
        // Center dot
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        this.ctx.beginPath();
        this.ctx.arc(x, y, 3, 0, Math.PI * 2);
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
