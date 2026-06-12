#!/usr/bin/env bash
# ============================================================================
#  ██████╗  ██████╗  ██████╗ ███████╗████████╗ █████╗
# ██╔════╝ ██╔═══██╗██╔════╝ ██╔════╝╚══██╔══╝██╔══██╗
# ██║  ███╗██║   ██║██║  ███╗█████╗     ██║   ███████║
# ██║   ██║██║   ██║██║   ██║██╔══╝     ██║   ██╔══██║
# ╚██████╔╝╚██████╔╝╚██████╔╝███████╗   ██║   ██║  ██║
#  ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝
# ============================================================================
# Gogeta Agent Installer for Linux / macOS
# ============================================================================
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/the1frombeyond/gogeta-agent/main/install.sh | bash
# ============================================================================

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────
GOGETA_HOME="${HOME}/.gogeta"
REPO_URL="https://github.com/the1frombeyond/gogeta-agent.git"
BRANCH="main"

# ── Colors ────────────────────────────────────────────────────────────────
C_RESET="\033[0m"
C_RED="\033[91m"
C_GREEN="\033[92m"
C_YEL="\033[93m"
C_BLUE="\033[94m"
C_MAG="\033[95m"
C_CYAN="\033[96m"
C_BOLD="\033[1m"
C_DIM="\033[2m"

# ── Banner ────────────────────────────────────────────────────────────────
show_banner() {
    clear 2>/dev/null || true
    cat << BANNER

${C_CYAN}    ██████╗  ██████╗  ██████╗ ███████╗████████╗ █████╗${C_RESET}
${C_CYAN}   ██╔════╝ ██╔═══██╗██╔════╝ ██╔════╝╚══██╔══╝██╔══██╗${C_RESET}
${C_CYAN}   ██║  ███╗██║   ██║██║  ███╗█████╗     ██║   ███████║${C_RESET}
${C_CYAN}   ██║   ██║██║   ██║██║   ██║██╔══╝     ██║   ██╔══██║${C_RESET}
${C_CYAN}   ╚██████╔╝╚██████╔╝╚██████╔╝███████╗   ██║   ██║  ██║${C_RESET}
${C_CYAN}    ╚═════╝  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝${C_RESET}
${C_BOLD}${C_YEL}       The Self-Improving AI Agent — v3.0${C_RESET}
${C_DIM}       Installing to: ${GOGETA_HOME}${C_RESET}

BANNER
}

log_step()   { printf "${C_CYAN}  ◆${C_RESET} %s${C_RESET}\n" "$*"; }
log_ok()     { printf "${C_GREEN}  ✓${C_RESET} %s${C_RESET}\n" "$*"; }
log_info()   { printf "${C_BLUE}  ℹ${C_RESET} %s${C_RESET}\n" "$*"; }
log_warn()   { printf "${C_YEL}  ⚠${C_RESET} %s${C_RESET}\n" "$*"; }
log_err()    { printf "${C_RED}  ✗${C_RESET} %s${C_RESET}\n" "$*" >&2; exit 1; }

# ── Prerequisites ─────────────────────────────────────────────────────────
check_prereqs() {
    log_step "Checking prerequisites..."

    command -v python3 >/dev/null 2>&1 || log_err "Python 3 not found. Install from https://python.org"
    pyver=$(python3 --version 2>&1)
    echo "$pyver" | grep -qE "Python 3\.(1[1-9]|[2-9][0-9])" || log_err "Python 3.11+ required (found $pyver)"
    log_ok "$pyver"

    command -v git >/dev/null 2>&1 || log_err "Git not found. Install from https://git-scm.com"
    log_ok "Git $(git --version 2>&1 | awk '{print $3}')"

    command -v node >/dev/null 2>&1 || log_err "Node.js not found. Install from https://nodejs.org"
    command -v npm >/dev/null 2>&1 || log_err "npm not found"
    log_ok "Node.js $(node --version) / npm $(npm --version)"
}

# ── Clone / Update ────────────────────────────────────────────────────────
install_repo() {
    if [ -d "$GOGETA_HOME/.git" ]; then
        log_step "Updating existing installation..."
        cd "$GOGETA_HOME"
        git pull origin "$BRANCH"
        log_ok "Repository updated"
    else
        log_step "Cloning Gogeta repository..."
        rm -rf "$GOGETA_HOME"
        git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$GOGETA_HOME"
        log_ok "Repository cloned"
    fi
}

# ── Setup venv ────────────────────────────────────────────────────────────
install_python() {
    log_step "Setting up Python virtual environment..."
    if [ ! -d "$GOGETA_HOME/.venv" ]; then
        python3 -m venv "$GOGETA_HOME/.venv"
    fi
    source "$GOGETA_HOME/.venv/bin/activate"
    pip install --upgrade pip -q
    pip install -e "$GOGETA_HOME" -q
    log_ok "Python dependencies installed"
}

# ── Build TUI ─────────────────────────────────────────────────────────────
install_tui() {
    if [ ! -d "$GOGETA_HOME/ui-tui" ]; then
        log_info "TUI directory not found, skipping"
        return
    fi
    log_step "Building Terminal UI..."
    cd "$GOGETA_HOME/ui-tui"
    npm install --silent
    npm run build
    cd "$GOGETA_HOME"
    log_ok "TUI built"
}

# ── Launcher ──────────────────────────────────────────────────────────────
install_launcher() {
    log_step "Creating launcher..."
    mkdir -p "${HOME}/.local/bin"
    LAUNCHER="${HOME}/.local/bin/gogeta"
    cat > "$LAUNCHER" << SCRIPT
#!/usr/bin/env bash
exec "\${HOME}/.gogeta/.venv/bin/gogeta" "\$@"
SCRIPT
    chmod +x "$LAUNCHER"
    log_ok "Launcher created at $LAUNCHER"

    case ":${PATH}:" in
        *:"${HOME}/.local/bin":*) ;;
        *)
            log_step "Adding ~/.local/bin to PATH..."
            rc_file=""
            if [ -n "${ZSH_VERSION-}" ]; then
                rc_file="${HOME}/.zshrc"
            elif [ -n "${BASH_VERSION-}" ]; then
                rc_file="${HOME}/.bashrc"
            elif [ -f "${HOME}/.config/fish/config.fish" ]; then
                rc_file="${HOME}/.config/fish/config.fish"
            fi
            if [ -n "$rc_file" ]; then
                echo "" >> "$rc_file"
                echo "# Gogeta" >> "$rc_file"
                echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> "$rc_file"
                log_ok "Added ~/.local/bin to PATH in $rc_file"
                log_info "Re-login or 'source $rc_file' to apply"
            fi
            ;;
    esac
}

# ── Cleanup ───────────────────────────────────────────────────────────────
remove_unwanted() {
    log_step "Cleaning up development-only folders..."
    local count=0
    for item in ".github" "tests" "website" "scripts" "release" \
                 "plans" ".plans" "infographic" "datagen-config-examples" \
                 "optional-mcps" "packaging" "nix" "TODO-NEXT-SESSION.md" \
                 "GOGETA_TUI_REDESIGN.md" "GOGETA_AUTONOMY_DIRECTIVE.md"; do
        if [ -e "$GOGETA_HOME/$item" ]; then
            rm -rf "$GOGETA_HOME/$item" 2>/dev/null && count=$((count + 1)) || true
        fi
    done
    log_ok "Cleaned up $count dev-only folders"
}

# ── Setup Wizard ──────────────────────────────────────────────────────────
invoke_setup() {
    echo ""
    log_step "Starting Gogeta setup wizard..."
    echo ""
    cd "$GOGETA_HOME"
    "$GOGETA_HOME/.venv/bin/python" -m gogeta_cli.main setup
}

# ── Success ───────────────────────────────────────────────────────────────
show_success() {
    echo ""
    printf "${C_GREEN}  ╔═══════════════════════════════════════════════╗${C_RESET}\n"
    printf "${C_GREEN}  ║${C_RESET}${C_BOLD}${C_YEL}      Gogeta Agent installed successfully!     ${C_RESET}${C_GREEN}║${C_RESET}\n"
    printf "${C_GREEN}  ╚═══════════════════════════════════════════════╝${C_RESET}\n"
    echo ""
    printf "  ${C_CYAN}Install path:${C_RESET}  ${GOGETA_HOME}\n"
    printf "  ${C_CYAN}Command:${C_RESET}       gogeta\n"
    printf "  ${C_CYAN}TUI:${C_RESET}           gogeta --tui\n"
    echo ""
    printf "  ${C_DIM}Run 'gogeta' anytime to chat with your agent.${C_RESET}\n"
    echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────
show_banner
check_prereqs
install_repo
install_python
install_tui
install_launcher
remove_unwanted
invoke_setup
show_success
