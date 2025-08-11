#!/bin/bash

# install.sh
# Description: Installation script for the Hiddify Telegram Bot.

# Define text colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
RESET='\033[0m' # Reset text color

# Configuration
HIDY_BOT_ID="@HidyBotGroup"
# Updated repository URL
REPOSITORY_URL="https://github.com/naseh42/hiddy.git"
INSTALL_DIR="/opt/Hiddify-Telegram-Bot"
BRANCH="main"

# Paths for logs and other directories
LOGS_DIR="$INSTALL_DIR/Logs"
RECEIPTS_DIR="$INSTALL_DIR/UserBot/Receiptions"
BACKUP_DIR="$INSTALL_DIR/Backup"
DATABASE_DIR="$INSTALL_DIR/Database"

# Log file
LOG_FILE="$LOGS_DIR/install.log"

# Function to display colored messages
function display_message() {
  local color=$1
  local message=$2
  echo -e "${color}${message}${RESET}"
  # Also log the message
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" >> "$LOG_FILE" 2>/dev/null || true
}

# Function to display error messages and exit
function display_error_and_exit() {
  display_message "$RED" "❌ Error: $1"
  display_message "$YELLOW" "💡 Support: ${HIDY_BOT_ID}"
  # Log the error
  echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" >> "$LOG_FILE" 2>/dev/null || true
  exit 1
}

# Function to log informational messages
function log_info() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO: $1" >> "$LOG_FILE" 2>/dev/null || true
}

# Function to detect OS and package manager
function detect_os() {
  display_message "$BLUE" "🔍 Detecting operating system..."
  log_info "Detecting operating system..."
  
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
    display_message "$BLUE" "✅ Detected OS: $OS $VER"
    log_info "Detected OS: $OS $VER"
  elif [ "$(uname -s)" == "Darwin" ]; then
    OS="macos"
    display_message "$BLUE" "✅ Detected OS: macOS"
    log_info "Detected OS: macOS"
  else
    display_message "$YELLOW" "⚠️ Unsupported OS detected. Proceeding with generic installation."
    log_info "Unsupported OS detected."
    OS="unknown"
  fi
}

# Function to install Git if needed
function install_git_if_needed() {
  display_message "$BLUE" "🔧 Checking Git installation..."
  log_info "Checking Git installation..."
  
  if ! command -v git &>/dev/null; then
    display_message "$YELLOW" "Git is not installed. Installing Git..."
    log_info "Git is not installed. Installing Git..."

    # Install Git based on the operating system (Linux)
    if [ -f /etc/os-release ]; then
      . /etc/os-release
      if [ "$ID" == "ubuntu" ] || [ "$ID" == "debian" ]; then
        display_message "$CYAN" "Installing Git on Ubuntu/Debian..."
        log_info "Installing Git on Ubuntu/Debian..."
        sudo apt update
        sudo apt install -y git
      elif [ "$ID" == "centos" ] || [ "$ID" == "rhel" ] || [ "$ID" == "fedora" ]; then
        display_message "$CYAN" "Installing Git on CentOS/RHEL/Fedora..."
        log_info "Installing Git on CentOS/RHEL/Fedora..."
        if [ "$ID" == "fedora" ]; then
          sudo dnf install -y git
        else
          sudo yum install -y git
        fi
      else
        display_error_and_exit "Unsupported Linux distribution for automatic Git installation. Please install Git manually."
      fi
    elif [ "$(uname -s)" == "Darwin" ]; then # macOS
      display_message "$CYAN" "Installing Git on macOS (requires Homebrew)..."
      log_info "Installing Git on macOS..."
      # Check if Homebrew is installed
      if ! command -v brew &>/dev/null; then
        display_error_and_exit "Homebrew is not installed. Please install Homebrew first: https://brew.sh/"
      fi
      brew install git
    else
      display_error_and_exit "Unsupported operating system. Please install Git manually and try again."
    fi

    if ! command -v git &>/dev/null; then
      display_error_and_exit "Failed to install Git. Please install Git manually and try again."
    fi

    display_message "$GREEN" "✅ Git has been installed successfully."
    log_info "Git has been installed successfully."
  else
    display_message "$GREEN" "✅ Git is already installed."
    log_info "Git is already installed."
  fi
}

# Function to install Python 3 and pip if they are not already installed
function install_python3_and_pip_if_needed() {
  display_message "$BLUE" "🐍 Checking Python 3 and pip installation..."
  log_info "Checking Python 3 and pip installation..."
  
  if ! command -v python3 &>/dev/null || ! command -v pip3 &>/dev/null; then
    display_message "$YELLOW" "Python 3 and/or pip are not installed. Installing Python 3 and pip..."
    log_info "Python 3 and/or pip are not installed. Installing Python 3 and pip..."

    # Install Python 3 and pip based on the operating system (Linux)
    if [ -f /etc/os-release ]; then
      . /etc/os-release
      if [ "$ID" == "ubuntu" ] || [ "$ID" == "debian" ]; then
        display_message "$CYAN" "Installing Python 3 and pip on Ubuntu/Debian..."
        log_info "Installing Python 3 and pip on Ubuntu/Debian..."
        sudo apt update
        sudo apt install -y python3 python3-pip
      elif [ "$ID" == "centos" ] || [ "$ID" == "rhel" ] || [ "$ID" == "fedora" ]; then
        display_message "$CYAN" "Installing Python 3 and pip on CentOS/RHEL/Fedora..."
        log_info "Installing Python 3 and pip on CentOS/RHEL/Fedora..."
        if [ "$ID" == "fedora" ]; then
          sudo dnf install -y python3 python3-pip
        else
          sudo yum install -y python3 python3-pip
        fi
      else
        display_error_and_exit "Unsupported Linux distribution for automatic Python 3 installation. Please install Python 3 and pip manually."
      fi
    elif [ "$(uname -s)" == "Darwin" ]; then # macOS
      display_message "$CYAN" "Installing Python 3 on macOS (requires Homebrew)..."
      log_info "Installing Python 3 on macOS..."
      # Check if Homebrew is installed
      if ! command -v brew &>/dev/null; then
        display_error_and_exit "Homebrew is not installed. Please install Homebrew first: https://brew.sh/"
      fi
      brew install python
    else
      display_error_and_exit "Unsupported operating system. Please install Python 3 and pip manually and try again."
    fi

    if ! command -v python3 &>/dev/null || ! command -v pip3 &>/dev/null; then
      display_error_and_exit "Failed to install Python 3 and pip. Please install Python 3 and pip manually and try again."
    fi

    display_message "$GREEN" "✅ Python 3 and pip have been installed successfully."
    log_info "Python 3 and pip have been installed successfully."
  else
    display_message "$GREEN" "✅ Python 3 and pip are already installed."
    log_info "Python 3 and pip are already installed."
    PYTHON_VERSION=$(python3 --version)
    PIP_VERSION=$(pip3 --version)
    display_message "$BLUE" "   Python version: $PYTHON_VERSION"
    display_message "$BLUE" "   Pip version: $PIP_VERSION"
    log_info "Python version: $PYTHON_VERSION"
    log_info "Pip version: $PIP_VERSION"
  fi
}

# Function to create necessary directories
function create_directories() {
  display_message "$BLUE" "📁 Creating necessary directories..."
  log_info "Creating necessary directories..."
  
  # Create main installation directory
  if [ ! -d "$INSTALL_DIR" ]; then
    display_message "$CYAN" "Creating directory: $INSTALL_DIR"
    log_info "Creating directory: $INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR"
    # Set ownership to the current user (if not root)
    if [ "$EUID" -ne 0 ]; then
      sudo chown -R $(whoami) "$INSTALL_DIR"
    fi
  else
    display_message "$GREEN" "✅ Directory $INSTALL_DIR already exists."
    log_info "Directory $INSTALL_DIR already exists."
  fi
  
  # Create subdirectories
  local dirs=("$LOGS_DIR" "$RECEIPTS_DIR" "$BACKUP_DIR" "$DATABASE_DIR")
  for dir in "${dirs[@]}"; do
    if [ ! -d "$dir" ]; then
      display_message "$CYAN" "Creating directory: $dir"
      log_info "Creating directory: $dir"
      mkdir -p "$dir"
    else
      display_message "$GREEN" "✅ Directory $dir already exists."
      log_info "Directory $dir already exists."
    fi
  done
}

# Function to clone or update the repository
function clone_or_update_repository() {
  display_message "$BLUE" "📥 Cloning or updating the repository..."
  log_info "Cloning or updating the repository..."
  
  # Check if directory is empty or not a git repo
  if [ ! -d "$INSTALL_DIR/.git" ]; then
    display_message "$CYAN" "Cloning repository from $REPOSITORY_URL to $INSTALL_DIR"
    log_info "Cloning repository from $REPOSITORY_URL to $INSTALL_DIR"
    
    # Remove contents of directory if it exists but is not a git repo
    if [ -d "$INSTALL_DIR" ] && [ "$(ls -A $INSTALL_DIR)" ]; then
      display_message "$YELLOW" "Directory $INSTALL_DIR is not empty and not a git repository. Removing contents..."
      log_info "Directory $INSTALL_DIR is not empty and not a git repository. Removing contents..."
      rm -rf "$INSTALL_DIR"/*
    fi
    
    # Clone the repository
    git clone -b "$BRANCH" "$REPOSITORY_URL" "$INSTALL_DIR" || display_error_and_exit "Failed to clone the repository."
    display_message "$GREEN" "✅ Repository cloned successfully."
    log_info "Repository cloned successfully."
  else
    display_message "$CYAN" "Repository already exists. Updating..."
    log_info "Repository already exists. Updating..."
    cd "$INSTALL_DIR" || display_error_and_exit "Failed to change directory to $INSTALL_DIR"
    
    # Stash any local changes
    git stash push -m "Stashed by install script before update"
    
    # Pull the latest changes
    git pull origin "$BRANCH" || display_error_and_exit "Failed to pull the latest changes from the repository."
    
    # Pop the stash if there were any changes (optional, might cause conflicts)
    # git stash pop
    
    display_message "$GREEN" "✅ Repository updated successfully."
    log_info "Repository updated successfully."
  fi
  
  # Change to the installation directory
  cd "$INSTALL_DIR" || display_error_and_exit "Failed to change directory to $INSTALL_DIR"
}

# Function to install Python requirements
function install_requirements() {
  display_message "$BLUE" "📦 Installing Python requirements from requirements.txt..."
  log_info "Installing Python requirements from requirements.txt..."
  
  # Check if requirements.txt exists
  if [ ! -f "requirements.txt" ]; then
    display_error_and_exit "requirements.txt not found in the repository."
  fi
  
  # Upgrade pip first
  display_message "$CYAN" "Upgrading pip..."
  log_info "Upgrading pip..."
  pip3 install --upgrade pip
  
  # Install requirements
  pip3 install -r requirements.txt || display_error_and_exit "Failed to install requirements from requirements.txt."
  
  display_message "$GREEN" "✅ Python requirements installed successfully."
  log_info "Python requirements installed successfully."
}

# Function to set executable permissions
function set_executable_permissions() {
  display_message "$BLUE" "🔐 Setting executable permissions for scripts..."
  log_info "Setting executable permissions for scripts..."
  
  # Make restart.sh and update.sh executable
  local scripts=("restart.sh" "update.sh")
  for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
      display_message "$CYAN" "Setting executable permission for $script"
      log_info "Setting executable permission for $script"
      chmod +x "$script"
    else
      display_message "$YELLOW" "⚠️ Script $script not found. Skipping..."
      log_info "Script $script not found. Skipping..."
    fi
  done
  
  display_message "$GREEN" "✅ Executable permissions set successfully."
  log_info "Executable permissions set successfully."
}

# Function to run initial configuration
function run_initial_configuration() {
  display_message "$BLUE" "⚙️ Running initial configuration (config.py)..."
  log_info "Running initial configuration (config.py)..."
  
  # Check if config.py exists
  if [ ! -f "config.py" ]; then
    display_error_and_exit "config.py not found in the repository."
  fi
  
  # Run config.py
  python3 config.py || display_error_and_exit "Failed to run config.py for initial configuration."
  
  display_message "$GREEN" "✅ Initial configuration completed successfully."
  log_info "Initial configuration completed successfully."
}

# Function to start the bot
function start_bot() {
  display_message "$BLUE" "🚀 Starting the bot in the background..."
  log_info "Starting the bot in the background..."
  
  # Stop any existing bot processes
  pkill -f "hiddifyTelegramBot.py" >/dev/null 2>&1 || true
  
  # Start the bot using nohup
  nohup python3 hiddifyTelegramBot.py >> "$INSTALL_DIR/bot.log" 2>&1 &
  BOT_PID=$!
  
  # Wait a moment for the process to start
  sleep 3
  
  # Check if the bot is running
  if ps -p $BOT_PID > /dev/null; then
    display_message "$GREEN" "✅ Bot started successfully with PID $BOT_PID."
    log_info "Bot started successfully with PID $BOT_PID."
    display_message "$GREEN" "📝 Log file is located at: $INSTALL_DIR/bot.log"
    log_info "Log file is located at: $INSTALL_DIR/bot.log"
    display_message "$GREEN" "💬 Send /start to your bot on Telegram to begin."
  else
    display_error_and_exit "Failed to start the bot. Please check the log file: $INSTALL_DIR/bot.log"
  fi
}

# Function to setup cron jobs
function setup_cron_jobs() {
  display_message "$BLUE" "⏰ Setting up cron jobs..."
  log_info "Setting up cron jobs..."
  
  # Function to add a cron job if it doesn't already exist
  add_cron_job_if_not_exists() {
    local cron_job="$1"
    local current_crontab

    # Normalize the cron job formatting (remove extra spaces)
    cron_job=$(echo "$cron_job" | sed -e 's/^[ \t]*//' -e 's/[ \t]*$//')

    # Get current crontab
    current_crontab=$(crontab -l 2>/dev/null || true)

    # Check if the cron job already exists
    if [[ -z "$current_crontab" ]]; then
      # No existing crontab, so add the new cron job
      (echo "$cron_job") | crontab -
      display_message "$CYAN" "Added cron job: $cron_job"
      log_info "Added cron job: $cron_job"
    elif ! (echo "$current_crontab" | grep -Fq "$cron_job"); then
      # Cron job doesn't exist, so append it to the crontab
      (echo "$current_crontab"; echo "$cron_job") | crontab -
      display_message "$CYAN" "Added cron job: $cron_job"
      log_info "Added cron job: $cron_job"
    else
      display_message "$GREEN" "✅ Cron job already exists: $cron_job"
      log_info "Cron job already exists: $cron_job"
    fi
  }

  # Add cron jobs
  # Start bot on reboot
  add_cron_job_if_not_exists "@reboot cd $INSTALL_DIR && ./restart.sh"
  
  # Backup every 6 hours
  add_cron_job_if_not_exists "0 */6 * * * cd $INSTALL_DIR && python3 crontab.py --backup"
  
  # Send reminders daily at 12:00 PM
  add_cron_job_if_not_exists "0 12 * * * cd $INSTALL_DIR && python3 crontab.py --reminder"
  
  display_message "$GREEN" "✅ Cron jobs set up successfully."
  log_info "Cron jobs set up successfully."
}

# Function to display final instructions
function display_final_instructions() {
  display_message "$PURPLE" "==============================================="
  display_message "$GREEN" "🎉 Hiddify Telegram Bot Installation Complete!"
  display_message "$PURPLE" "==============================================="
  display_message "$BLUE" "📁 Installation Directory: $INSTALL_DIR"
  display_message "$BLUE" "📝 Log File: $INSTALL_DIR/bot.log"
  display_message "$BLUE" "⚙️  To manage the bot, use the following commands:"
  display_message "$CYAN" "   cd $INSTALL_DIR && ./restart.sh     # Restart the bot"
  display_message "$CYAN" "   cd $INSTALL_DIR && ./update.sh      # Update the bot"
  display_message "$CYAN" "   tail -f $INSTALL_DIR/bot.log        # View bot logs"
  display_message "$YELLOW" "💬 Don't forget to send /start to your bot on Telegram!"
  display_message "$YELLOW" "💡 For support, contact: ${HIDY_BOT_ID}"
  display_message "$PURPLE" "==============================================="
}

# Main installation function
function main() {
  # Create logs directory early for logging
  mkdir -p "$LOGS_DIR"
  
  display_message "$PURPLE" "==============================================="
  display_message "$GREEN" "🚀 Starting Hiddify Telegram Bot Installation"
  display_message "$PURPLE" "==============================================="
  log_info "==============================================="
  log_info "Starting Hiddify Telegram Bot Installation"
  log_info "==============================================="
  
  # Step 0: Check requirements
  display_message "$BLUE" "🔍 Step 0: Checking system requirements..."
  log_info "Step 0: Checking system requirements..."
  detect_os
  install_git_if_needed
  install_python3_and_pip_if_needed
  
  # Step 1: Create directories
  display_message "$BLUE" "📁 Step 1: Creating directories..."
  log_info "Step 1: Creating directories..."
  create_directories
  
  # Step 2: Clone or update repository
  display_message "$BLUE" "📥 Step 2: Cloning or updating repository..."
  log_info "Step 2: Cloning or updating repository..."
  clone_or_update_repository
  
  # Step 3: Install requirements
  display_message "$BLUE" "📦 Step 3: Installing requirements..."
  log_info "Step 3: Installing requirements..."
  install_requirements
  
  # Step 4: Set permissions
  display_message "$BLUE" "🔐 Step 4: Setting permissions..."
  log_info "Step 4: Setting permissions..."
  set_executable_permissions
  
  # Step 5: Run initial configuration
  display_message "$BLUE" "⚙️ Step 5: Running initial configuration..."
  log_info "Step 5: Running initial configuration..."
  run_initial_configuration
  
  # Step 6: Start the bot
  display_message "$BLUE" "🚀 Step 6: Starting the bot..."
  log_info "Step 6: Starting the bot..."
  start_bot
  
  # Step 7: Setup cron jobs
  display_message "$BLUE" "⏰ Step 7: Setting up cron jobs..."
  log_info "Step 7: Setting up cron jobs..."
  setup_cron_jobs
  
  # Final instructions
  display_final_instructions
  
  log_info "Installation completed successfully."
}

# Run the main function
main "$@"
