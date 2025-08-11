#!/bin/bash

# restart.sh
# Description: Script to restart the Hiddify Telegram Bot gracefully.

# Define text colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
RESET='\033[0m' # Reset text color

# Configuration
INSTALL_DIR="/opt/Hiddify-Telegram-Bot"
BOT_SCRIPT="hiddifyTelegramBot.py"
LOG_FILE="$INSTALL_DIR/bot.log"
PID_FILE="$INSTALL_DIR/bot.pid"

# Function to display colored messages
function display_message() {
  local color=$1
  local message=$2
  echo -e "${color}${message}${RESET}"
}

# Function to display error messages and exit
function display_error_and_exit() {
  display_message "$RED" "❌ Error: $1"
  exit 1
}

# Function to display warning messages
function display_warning() {
  display_message "$YELLOW" "⚠️ Warning: $1"
}

# Function to display info messages
function display_info() {
  display_message "$BLUE" "ℹ️ Info: $1"
}

# Function to check if a command exists
function command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
function check_prerequisites() {
  display_message "$BLUE" "🔍 Checking prerequisites..."
  
  # Check if Python 3 is installed
  if ! command_exists python3; then
    display_error_and_exit "Python 3 is required. Please install it and try again."
  fi
  
  # Check if the installation directory exists
  if [ ! -d "$INSTALL_DIR" ]; then
    display_error_and_exit "Installation directory $INSTALL_DIR does not exist."
  fi
  
  # Check if the bot script exists
  if [ ! -f "$INSTALL_DIR/$BOT_SCRIPT" ]; then
    display_error_and_exit "Bot script $BOT_SCRIPT not found in $INSTALL_DIR."
  fi
  
  display_message "$GREEN" "✅ Prerequisites checked successfully."
}

# Function to stop the bot gracefully
function stop_bot() {
  display_message "$BLUE" "⏹️ Stopping the bot gracefully..."
  
  # Method 1: Try to stop using PID file (if it exists and is valid)
  if [ -f "$PID_FILE" ]; then
    BOT_PID=$(cat "$PID_FILE")
    if [ ! -z "$BOT_PID" ] && kill -0 "$BOT_PID" 2>/dev/null; then
      display_message "$CYAN" "Sending SIGTERM to process PID $BOT_PID..."
      kill -15 "$BOT_PID"
      
      # Wait for graceful shutdown (up to 10 seconds)
      local counter=0
      while kill -0 "$BOT_PID" 2>/dev/null && [ $counter -lt 10 ]; do
        sleep 1
        ((counter++))
      done
      
      # If still running, force kill
      if kill -0 "$BOT_PID" 2>/dev/null; then
        display_warning "Process $BOT_PID did not stop gracefully. Forcing termination..."
        kill -9 "$BOT_PID"
        sleep 2
      fi
      
      # Remove PID file
      rm -f "$PID_FILE"
    else
      display_warning "PID file exists but process is not running or invalid. Cleaning up..."
      rm -f "$PID_FILE"
    fi
  fi
  
  # Method 2: Fallback - Use pkill to stop any running instances
  if pgrep -f "$BOT_SCRIPT" > /dev/null; then
    display_message "$CYAN" "Terminating bot processes using pkill..."
    pkill -15 -f "$BOT_SCRIPT"
    
    # Wait a moment for processes to terminate
    sleep 3
    
    # Force kill any remaining processes
    if pgrep -f "$BOT_SCRIPT" > /dev/null; then
      display_warning "Some bot processes are still running. Forcing termination..."
      pkill -9 -f "$BOT_SCRIPT"
      sleep 2
    fi
  else
    display_message "$GREEN" "✅ Bot is not currently running."
  fi
  
  display_message "$GREEN" "⏹️ Bot stopped successfully."
}

# Function to start the bot
function start_bot() {
  display_message "$BLUE" "🚀 Starting the bot..."
  
  # Change to the installation directory
  cd "$INSTALL_DIR" || display_error_and_exit "Failed to change directory to $INSTALL_DIR"
  
  # Clear the previous log file content (optional)
  # Uncomment the next line if you want to clear logs on each restart
  # > "$LOG_FILE"
  
  # Start the bot in the background using nohup
  display_message "$CYAN" "Starting bot process..."
  nohup python3 "$INSTALL_DIR/$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
  NEW_BOT_PID=$!
  
  # Save the PID to a file
  echo $NEW_BOT_PID > "$PID_FILE"
  
  # Wait briefly to ensure the process has started
  sleep 3
  
  # Check if the bot is running
  if ps -p $NEW_BOT_PID > /dev/null; then
    display_message "$GREEN" "✅ Bot started successfully with PID $NEW_BOT_PID."
    display_message "$GREEN" "📝 Log file: $LOG_FILE"
    display_message "$GREEN" "🔗 PID file: $PID_FILE"
  else
    display_error_and_exit "Failed to start the bot. Please check the log file: $LOG_FILE"
  fi
}

# Function to restart the bot
function restart_bot() {
  display_message "$PURPLE" "==============================================="
  display_message "$GREEN" "🔄 Restarting Hiddify Telegram Bot"
  display_message "$PURPLE" "==============================================="
  
  check_prerequisites
  stop_bot
  display_message "$YELLOW" "⏳ Waiting for 5 seconds before starting..."
  sleep 5
  start_bot
  
  display_message "$PURPLE" "==============================================="
  display_message "$GREEN" "🎉 Bot restart completed successfully!"
  display_message "$PURPLE" "==============================================="
}

# Function to show bot status
function show_status() {
  display_message "$BLUE" "📊 Checking bot status..."
  
  if [ -f "$PID_FILE" ]; then
    BOT_PID=$(cat "$PID_FILE")
    if [ ! -z "$BOT_PID" ] && kill -0 "$BOT_PID" 2>/dev/null; then
      display_message "$GREEN" "✅ Bot is running with PID $BOT_PID"
    else
      display_warning "PID file exists but process is not running. Bot may have crashed."
      rm -f "$PID_FILE"
    fi
  elif pgrep -f "$BOT_SCRIPT" > /dev/null; then
    PIDS=$(pgrep -f "$BOT_SCRIPT")
    display_message "$GREEN" "✅ Bot is running with PID(s): $PIDS"
    display_warning "Note: PID file not found. Consider restarting for proper management."
  else
    display_message "$YELLOW" " Bot is not running."
  fi
}

# Function to show help
function show_help() {
  echo "Usage: $0 [option]"
  echo "Options:"
  echo "  start     Start the bot"
  echo "  stop      Stop the bot"
  echo "  restart   Restart the bot (default)"
  echo "  status    Show bot status"
  echo "  help      Show this help message"
}

# Main execution
case "${1:-restart}" in
  start)
    check_prerequisites
    start_bot
    ;;
  stop)
    check_prerequisites
    stop_bot
    ;;
  restart)
    restart_bot
    ;;
  status)
    show_status
    ;;
  help|--help|-h)
    show_help
    ;;
  *)
    display_warning "Invalid option: $1"
    show_help
    exit 1
    ;;
esac
