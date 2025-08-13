// Tutorial System for SATB Writing Website
class TutorialSystem {
    constructor() {
        this.currentStep = 0;
        this.isActive = false;
        this.tutorialSteps = [
            {
                title: "Welcome to SATB Writer!",
                content: "This tool helps you create beautiful 4-part harmony from a bass line. Let's get started!",
                target: null,
                position: "center"
            },
            {
                title: "Choose Your Key",
                content: "First, select the key for your piece. This helps the system understand the harmonic context.",
                target: ".key-dropdown",
                position: "bottom"
            },
            {
                title: "Input Your Bass Line",
                content: "Click on the staff to add bass notes. You can also use the keyboard shortcuts or note buttons below.",
                target: ".bass-line-section",
                position: "bottom"
            },
            {
                title: "Analyze Your Bass Line",
                content: "Click 'Analyze Bass Line' to see possible chord progressions that fit your bass notes.",
                target: ".bass-line-section:nth-of-type(2)",
                position: "bottom"
            },
            {
                title: "Choose a Progression",
                content: "Select a chord progression that sounds good to you. Each option shows different harmonic possibilities.",
                target: ".progression-suggestions",
                position: "top"
            },
            {
                title: "Generate SATB",
                content: "Click 'Generate SATB' to create beautiful 4-part harmony with proper voice leading.",
                target: "#satbOutput",
                position: "top"
            },
            {
                title: "Review Your Results",
                content: "Check the validation results to see how well your harmonization follows music theory rules.",
                target: ".validation-results",
                position: "top"
            },
            {
                title: "You're Ready!",
                content: "Congratulations! You now know how to use SATB Writer. Try creating your own harmonization!",
                target: null,
                position: "center"
            }
        ];
    }

    start() {
        try {
            console.log('Tutorial start called'); // Debug log
            this.isActive = true;
            this.currentStep = 0;
            this.createOverlay();
            this.showStep();
        } catch (error) {
            console.error('Error starting tutorial:', error);
        }
    }

    createOverlay() {
        // Remove existing overlay if any
        const existingOverlay = document.getElementById('tutorialOverlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }

        // Create overlay
        const overlay = document.createElement('div');
        overlay.id = 'tutorialOverlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s ease-in-out;
        `;

        // Create tutorial box
        const tutorialBox = document.createElement('div');
        tutorialBox.id = 'tutorialBox';
        tutorialBox.style.cssText = `
            background: white;
            border-radius: 8px;
            padding: 24px;
            max-width: 480px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 10000;
            border: 1px solid #e2e8f0;
            opacity: 0;
            transition: opacity 0.3s ease-in-out;
            will-change: opacity;
        `;

        overlay.appendChild(tutorialBox);
        document.body.appendChild(overlay);

        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            position: absolute;
            top: 10px;
            right: 15px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
        `;
        closeBtn.onclick = () => this.stop();
        tutorialBox.appendChild(closeBtn);

        this.overlay = overlay;
        this.tutorialBox = tutorialBox;

        // Trigger fade-in animation
        setTimeout(() => {
            overlay.style.opacity = '1';
            tutorialBox.style.opacity = '1';
        }, 10);
    }

    showStep() {
        if (!this.isActive || this.currentStep >= this.tutorialSteps.length) {
            this.stop();
            return;
        }

        const step = this.tutorialSteps[this.currentStep];
        
        // Update tutorial box content
        this.tutorialBox.innerHTML = `
            <button onclick="tutorial.stop()" style="position: absolute; top: 12px; right: 16px; background: none; border: none; font-size: 20px; cursor: pointer; color: #94a3b8; font-weight: 300;">×</button>
            <h2 style="color: #1e293b; margin-bottom: 12px; font-size: 20px; font-weight: 600;">${step.title}</h2>
            <p style="color: #64748b; line-height: 1.6; margin-bottom: 20px; font-size: 14px;">${step.content}</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="color: #94a3b8; font-size: 12px; font-weight: 500;">
                    Step ${this.currentStep + 1} of ${this.tutorialSteps.length}
                </div>
                <div>
                    ${this.currentStep > 0 ? '<button onclick="tutorial.previousStep()" style="background: #64748b; color: white; border: none; padding: 8px 16px; border-radius: 4px; margin-right: 8px; cursor: pointer; font-size: 13px; font-weight: 500;">Previous</button>' : ''}
                    <button onclick="tutorial.nextStep()" style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-right: 8px; font-size: 13px; font-weight: 500;">
                        ${this.currentStep === this.tutorialSteps.length - 1 ? 'Finish' : 'Next'}
                    </button>
                    <button onclick="tutorial.stop()" style="background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 500;">
                        Skip
                    </button>
                </div>
            </div>
        `;

        // Tutorial box is already centered from creation, no need to reposition
    }

    // Tutorial box stays centered - no repositioning needed

    nextStep() {
        try {
            this.currentStep++;
            console.log('Moving to step:', this.currentStep); // Debug log
            this.showStep();
        } catch (error) {
            console.error('Error in nextStep:', error);
            this.stop();
        }
    }

    previousStep() {
        this.currentStep--;
        this.showStep();
    }

    stop() {
        this.isActive = false;
        if (this.overlay) {
            // Fade out before removing
            this.overlay.style.opacity = '0';
            this.tutorialBox.style.opacity = '0';
            setTimeout(() => {
                this.overlay.remove();
            }, 300);
        }
        // Don't save tutorial completion - show it every time
    }
}

// Initialize tutorial system
const tutorial = new TutorialSystem();

// Show tutorial every time the page loads
function checkTutorialStatus() {
    // Show tutorial immediately when page loads (every time)
    setTimeout(() => {
        console.log('Starting tutorial...'); // Debug log
        tutorial.start();
    }, 300);
}

// Add tutorial button to page
function addTutorialButton() {
    const tutorialBtn = document.createElement('button');
    tutorialBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 6px;"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>Help';
    tutorialBtn.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #1e293b;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 13px;
        font-weight: 500;
        z-index: 1000;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        transition: all 0.2s ease;
    `;
    
    // Add hover effect
    tutorialBtn.addEventListener('mouseenter', () => {
        tutorialBtn.style.background = '#374151';
        tutorialBtn.style.transform = 'translateY(-1px)';
        tutorialBtn.style.boxShadow = '0 2px 6px rgba(0,0,0,0.15)';
    });
    
    tutorialBtn.addEventListener('mouseleave', () => {
        tutorialBtn.style.background = '#1e293b';
        tutorialBtn.style.transform = 'translateY(0)';
        tutorialBtn.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
    });
    
    tutorialBtn.onclick = () => {
        // Start tutorial directly
        tutorial.start();
    };
    document.body.appendChild(tutorialBtn);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    addTutorialButton();
    checkTutorialStatus();
});
