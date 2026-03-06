#!/bin/bash
###############################################################################
# Interview Prep Coach - Linux Installer
#
# This script installs Interview Prep Coach and integrates it with Claude Code
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

###############################################################################
# Pre-flight Checks
###############################################################################

preflight_checks() {
    print_header "Pre-flight Checks"

    local all_good=true

    # Check Python version
    if check_command python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
            print_success "Python $PYTHON_VERSION found"
        else
            print_error "Python 3.10+ required (found $PYTHON_VERSION)"
            all_good=false
        fi
    else
        print_error "Python 3 not found"
        print_info "Install Python: sudo apt install python3 python3-pip"
        all_good=false
    fi

    # Check pip
    if check_command pip3 || check_command pip; then
        print_success "pip found"
    else
        print_error "pip not found"
        print_info "Install pip: sudo apt install python3-pip"
        all_good=false
    fi

    # Check for wheel file
    WHEEL_FILE=$(ls "$SCRIPT_DIR"/dist/interview_prep_coach-*-py3-none-any.whl 2>/dev/null | head -n1)
    if [ -f "$WHEEL_FILE" ]; then
        print_success "Package found: $(basename "$WHEEL_FILE")"
    else
        print_error "Package not found in dist/ directory"
        print_info "Run: python3 -m build"
        all_good=false
    fi

    # Check Claude Code
    if [ -d "$HOME/.claude" ]; then
        print_success "Claude Code directory found"
    else
        print_warning "Claude Code directory not found (~/.claude)"
        print_info "Claude Code integration will be available after Claude Code is installed"
    fi

    echo ""

    if [ "$all_good" = false ]; then
        print_error "Pre-flight checks failed. Please fix the issues above."
        exit 1
    fi
}

###############################################################################
# Installation
###############################################################################

install_package() {
    print_header "Installing Interview Prep Coach"

    # Uninstall old version if exists
    if pip3 show interview-prep-coach &> /dev/null; then
        print_info "Removing old version..."
        pip3 uninstall -y interview-prep-coach || true
    fi

    # Install package
    print_info "Installing package..."
    if pip3 install --force-reinstall "$WHEEL_FILE"; then
        print_success "Package installed successfully"
    else
        print_error "Package installation failed"
        exit 1
    fi

    echo ""
}

configure_claude_code() {
    print_header "Configuring Claude Code Integration"

    if [ ! -d "$HOME/.claude" ]; then
        print_warning "Claude Code not installed yet"
        print_info "Run 'interview-prep-coach install' after installing Claude Code"
        echo ""
        return
    fi

    # Run installer
    print_info "Integrating with Claude Code..."
    if interview-prep-coach install --force; then
        print_success "Claude Code integration complete"
    else
        print_error "Claude Code integration failed"
        print_info "You can run 'interview-prep-coach install' manually later"
    fi

    echo ""
}

###############################################################################
# Post-Installation
###############################################################################

show_completion() {
    print_header "Installation Complete!"

    echo ""
    print_success "Interview Prep Coach has been installed"
    echo ""

    print_info "Next steps:"
    echo "  1. Restart Claude Code for changes to take effect"
    echo "  2. Start Claude Code: claude"
    echo "  3. Use the /prep command"
    echo ""

    print_info "Available commands:"
    echo "  /prep              - Continue last session"
    echo "  /prep weak         - Practice weak areas"
    echo "  /prep mock         - Mock interview mode"
    echo "  /prep section Java - Practice specific section"
    echo ""

    print_info "Management commands:"
    echo "  interview-prep-coach status      - Check installation status"
    echo "  interview-prep-coach materials   - Manage question materials"
    echo "  interview-prep-coach uninstall   - Remove from Claude Code"
    echo ""

    print_warning "IMPORTANT: Restart Claude Code now!"
    echo ""
}

verify_installation() {
    print_header "Verifying Installation"

    # Check commands
    if check_command interview-prep-coach; then
        print_success "CLI command available: interview-prep-coach"
    else
        print_error "CLI command not found in PATH"
        print_info "You may need to restart your shell or add ~/.local/bin to PATH"
    fi

    if check_command interview-prep-coach-server; then
        print_success "MCP server available: interview-prep-coach-server"
    else
        print_warning "MCP server command not found (may need PATH update)"
    fi

    # Check installation status
    if interview-prep-coach status &> /dev/null; then
        print_success "Package is functioning correctly"
    else
        print_warning "Package installed but status check failed"
    fi

    echo ""
}

###############################################################################
# Uninstaller
###############################################################################

uninstall() {
    print_header "Uninstalling Interview Prep Coach"

    echo ""
    read -p "Remove user data (database, progress)? [y/N]: " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing Claude Code integration and user data..."
        interview-prep-coach uninstall --remove-data || true
    else
        print_info "Removing Claude Code integration (preserving data)..."
        interview-prep-coach uninstall || true
    fi

    print_info "Uninstalling Python package..."
    pip3 uninstall -y interview-prep-coach || true

    print_success "Uninstallation complete"
    print_warning "Restart Claude Code for changes to take effect"
    echo ""
}

###############################################################################
# Main Script
###############################################################################

show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install    - Install Interview Prep Coach (default)"
    echo "  uninstall  - Uninstall Interview Prep Coach"
    echo "  help       - Show this help message"
    echo ""
}

main() {
    # Banner
    echo ""
    print_header "Interview Prep Coach Installer"
    echo ""

    # Parse command
    COMMAND="${1:-install}"

    case "$COMMAND" in
        install)
            preflight_checks
            install_package
            verify_installation
            configure_claude_code
            show_completion
            ;;
        uninstall)
            uninstall
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
