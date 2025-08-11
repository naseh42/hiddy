#!/bin/bash
# update.sh
# Description: Script to update the Hiddify Telegram Bot.

# shellcheck disable=SC2034
# TARGET_VERSION will be dynamically determined from version.py
TARGET_VERSION=""
CURRENT_VERSION=""
INSTALL_DIR="/opt/Hiddify-Telegram-Bot"
BACKUP_DIR="$INSTALL_DIR/Backup"
LOG_FILE="$INSTALL_DIR/Logs/update.log"

# Define text colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m' # Reset text color

HIDY_BOT_ID="@HidyBotGroup"

# Function to display colored messages
function display_message() {
  local color=$1
  local message=$2
  echo -e "${color}${message}${RESET}"
  
  # Also log the message if LOG_FILE is set and writable
  if [[ -n "$LOG_FILE" ]] && touch "$LOG_FILE" 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $message" >> "$LOG_FILE"
  fi
}

# Function to display error messages and exit
function display_error_and_exit() {
  display_message "$RED" "❌ Error: $1"
  display_message "$YELLOW" "💡 Support: ${HIDY_BOT_ID}"
  
  # Also log the error
  if [[ -n "$LOG_FILE" ]] && touch "$LOG_FILE" 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" >> "$LOG_FILE"
  fi
  
  exit 1
}

# Function to log informational messages
function log_info() {
  if [[ -n "$LOG_FILE" ]] && touch "$LOG_FILE" 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - INFO: $1" >> "$LOG_FILE"
  fi
}

# Function to check prerequisites
function check_prerequisites() {
  display_message "$BLUE" "🔍 Checking prerequisites..."
  log_info "Checking prerequisites..."
  
  # Check if Git is installed
  if ! command -v git &>/dev/null; then
    display_error_and_exit "Git is not installed. Please install Git and try again."
  fi
  
  # Check if Python 3 is installed
  if ! command -v python3 &>/dev/null; then
    display_error_and_exit "Python 3 is not installed. Please install Python 3 and try again."
  fi
  
  # Check if pip is installed
  if ! command -v pip3 &>/dev/null; then
    display_error_and_exit "pip3 is not installed. Please install pip3 and try again."
  fi
  
  # Check if the installation directory exists
  if [ ! -d "$INSTALL_DIR" ]; then
    display_error_and_exit "Installation directory $INSTALL_DIR does not exist. Please install the bot first."
  fi
  
  display_message "$GREEN" "✅ Prerequisites checked successfully."
  log_info "Prerequisites checked successfully."
}

# Function to gracefully stop the bot
function stop_bot() {
  display_message "$BLUE" "⏹️ Stopping the bot gracefully..."
  log_info "Stopping the bot gracefully..."
  
  # Method 1: Try to stop using PID file (if it exists and is valid)
  local pid_file="$INSTALL_DIR/bot.pid"
  if [ -f "$pid_file" ]; then
    BOT_PID=$(cat "$pid_file")
    if [ ! -z "$BOT_PID" ] && kill -0 "$BOT_PID" 2>/dev/null; then
      display_message "$CYAN" "Sending SIGTERM to process PID $BOT_PID..."
      log_info "Sending SIGTERM to process PID $BOT_PID..."
      kill -15 "$BOT_PID"
      
      # Wait for graceful shutdown (up to 10 seconds)
      local counter=0
      while kill -0 "$BOT_PID" 2>/dev/null && [ $counter -lt 10 ]; do
        sleep 1
        ((counter++))
      done
      
      # If still running, force kill
      if kill -0 "$BOT_PID" 2>/dev/null; then
        display_message "$YELLOW" "Process $BOT_PID did not stop gracefully. Forcing termination..."
        log_info "Process $BOT_PID did not stop gracefully. Forcing termination..."
        kill -9 "$BOT_PID"
        sleep 2
      fi
      
      # Remove PID file
      rm -f "$pid_file"
    else
      display_message "$YELLOW" "PID file exists but process is not running or invalid. Cleaning up..."
      log_info "PID file exists but process is not running or invalid. Cleaning up..."
      rm -f "$pid_file"
    fi
  fi
  
  # Method 2: Fallback - Use pkill to stop any running instances
  if pgrep -f "hiddifyTelegramBot.py" > /dev/null; then
    display_message "$CYAN" "Terminating bot processes using pkill..."
    log_info "Terminating bot processes using pkill..."
    pkill -15 -f "hiddifyTelegramBot.py"
    
    # Wait a moment for processes to terminate
    sleep 3
    
    # Force kill any remaining processes
    if pgrep -f "hiddifyTelegramBot.py" > /dev/null; then
      display_message "$YELLOW" "Some bot processes are still running. Forcing termination..."
      log_info "Some bot processes are still running. Forcing termination..."
      pkill -9 -f "hiddifyTelegramBot.py"
      sleep 2
    fi
  else
    display_message "$GREEN" "✅ Bot is not currently running."
    log_info "Bot is not currently running."
  fi
  
  display_message "$GREEN" "⏹️ Bot stopped successfully."
  log_info "Bot stopped successfully."
}

# Function to get backup of Database/hidyBot.db
function get_backup() {
  display_message "$BLUE" "💾 Getting backup of Database/hidyBot.db..."
  log_info "Getting backup of Database/hidyBot.db..."
  
  local db_file="$INSTALL_DIR/Database/hidyBot.db"
  local backup_file="$BACKUP_DIR/hidyBot_$(date +%Y%m%d_%H%M%S).db.bak"
  
  # Create backup directory if it doesn't exist
  mkdir -p "$BACKUP_DIR"
  
  if [ -f "$db_file" ]; then
    if cp "$db_file" "$backup_file"; then
      display_message "$GREEN" "✅ Backup of Database/hidyBot.db has been taken: $backup_file"
      log_info "Backup of Database/hidyBot.db has been taken: $backup_file"
    else
      display_message "$RED" "❌ Failed to get backup of Database/hidyBot.db."
      log_info "Failed to get backup of Database/hidyBot.db."
      return 1
    fi
  else
    display_message "$YELLOW" "⚠️ Database file $db_file not found. Skipping database backup."
    log_info "Database file $db_file not found. Skipping database backup."
  fi
}

# Function to update the bot
function update_bot() {
  display_message "$BLUE" "🔄 Updating the bot..."
  log_info "Updating the bot..."
  
  # Change to the installation directory
  cd "$INSTALL_DIR" || display_error_and_exit "Failed to change directory to $INSTALL_DIR"
  
  # Stash any local changes
  display_message "$CYAN" "Stashing any local changes..."
  log_info "Stashing any local changes..."
  git stash push -m "Stashed by update script before update"
  
  # Determine branch
  local branch="main"
  if [ "$0" == "--pre-release" ]; then
    branch="pre-release"
  fi
  display_message "$CYAN" "Selected branch: $branch"
  log_info "Selected branch: $branch"
  
  # Pull the latest changes
  display_message "$CYAN" "Pulling the latest changes from $branch..."
  log_info "Pulling the latest changes from $branch..."
  if git pull origin "$branch"; then
    display_message "$GREEN" "✅ Successfully pulled the latest changes."
    log_info "Successfully pulled the latest changes."
  else
    display_message "$YELLOW" "⚠️ Failed to pull changes. Trying rebase..."
    log_info "Failed to pull changes. Trying rebase..."
    if git pull --rebase origin "$branch"; then
      display_message "$GREEN" "✅ Successfully rebased and pulled the latest changes."
      log_info "Successfully rebased and pulled the latest changes."
    else
      display_error_and_exit "Failed to update the bot. Check the Git repository for errors."
    fi
  fi
  
  # Update requirements
  display_message "$CYAN" "Updating Python requirements..."
  log_info "Updating Python requirements..."
  if pip3 install -r requirements.txt; then
    display_message "$GREEN" "✅ Python requirements updated successfully."
    log_info "Python requirements updated successfully."
  else
    display_error_and_exit "Failed to update Python requirements."
  fi
  
  display_message "$GREEN" "✅ Bot has been updated."
  log_info "Bot has been updated."
}

# Function to restart the bot
function restart_bot() {
  display_message "$BLUE" "🚀 Restarting the bot..."
  log_info "Restarting the bot..."
  
  # Change to the installation directory
  cd "$INSTALL_DIR" || display_error_and_exit "Failed to change directory to $INSTALL_DIR"
  
  # Clear the previous log file content (optional)
  # Uncomment the next line if you want to clear logs on each restart
  # > "$INSTALL_DIR/bot.log"
  
  # Start the bot in the background using nohup
  display_message "$CYAN" "Starting bot process..."
  log_info "Starting bot process..."
  nohup python3 "$INSTALL_DIR/hiddifyTelegramBot.py" >> "$INSTALL_DIR/bot.log" 2>&1 &
  NEW_BOT_PID=$!
  
  # Save the PID to a file
  echo $NEW_BOT_PID > "$INSTALL_DIR/bot.pid"
  
  # Wait briefly to ensure the process has started
  sleep 3
  
  # Check if the bot is running
  if ps -p $NEW_BOT_PID > /dev/null; then
    display_message "$GREEN" "✅ Bot restarted successfully with PID $NEW_BOT_PID."
    display_message "$GREEN" "📝 Log file: $INSTALL_DIR/bot.log"
    log_info "Bot restarted successfully with PID $NEW_BOT_PID."
  else
    display_error_and_exit "Failed to restart the bot. Please check the log file: $INSTALL_DIR/bot.log"
  fi
}

# Function to add cron jobs
function add_cron_jobs() {
  display_message "$BLUE" "⏰ Adding/updating cron jobs..."
  log_info "Adding/updating cron jobs..."
  
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
  
  display_message "$GREEN" "✅ Cron jobs added/updated successfully."
  log_info "Cron jobs added/updated successfully."
}

# Function to run database updates
function run_database_updates() {
  display_message "$BLUE" "🗄️ Running database updates..."
  log_info "Running database updates..."
  
  # Get current and target versions
  if [ -f "$INSTALL_DIR/version.py" ]; then
    CURRENT_VERSION=$(python3 "$INSTALL_DIR/version.py" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+(-[^ ]+)?' | head -1)
    if [ -z "$CURRENT_VERSION" ]; then
      display_message "$YELLOW" "⚠️ Could not determine current version from version.py. Using fallback method."
      log_info "Could not determine current version from version.py. Using fallback method."
      # Fallback: Try to get version directly from the file
      CURRENT_VERSION=$(grep -oE '^ *__version__ *= *"[^"]*"' "$INSTALL_DIR/version.py" | cut -d'"' -f2)
    fi
  else
    display_message "$YELLOW" "⚠️ version.py not found. Cannot determine current version."
    log_info "version.py not found. Cannot determine current version."
    CURRENT_VERSION="0.0.0"
  fi
  
  # TARGET_VERSION is now determined dynamically from the updated version.py
  if [ -f "$INSTALL_DIR/version.py" ]; then
    TARGET_VERSION=$(python3 "$INSTALL_DIR/version.py" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+(-[^ ]+)?' | head -1)
    if [ -z "$TARGET_VERSION" ]; then
      display_message "$YELLOW" "⚠️ Could not determine target version from updated version.py. Using fallback method."
      log_info "Could not determine target version from updated version.py. Using fallback method."
      # Fallback: Try to get version directly from the file
      TARGET_VERSION=$(grep -oE '^ *__version__ *= *"[^"]*"' "$INSTALL_DIR/version.py" | cut -d'"' -f2)
    fi
  else
    display_message "$YELLOW" "⚠️ Updated version.py not found. Cannot determine target version."
    log_info "Updated version.py not found. Cannot determine target version."
    TARGET_VERSION="0.0.0"
  fi
  
  display_message "$CYAN" "Current version: $CURRENT_VERSION"
  display_message "$CYAN" "Target version: $TARGET_VERSION"
  log_info "Current version: $CURRENT_VERSION"
  log_info "Target version: $TARGET_VERSION"
  
  # Run update.py if it exists
  if [ -f "$INSTALL_DIR/update.py" ]; then
    display_message "$CYAN" "Running update.py to handle database migrations..."
    log_info "Running update.py to handle database migrations..."
    
    if python3 "$INSTALL_DIR/update.py" --current-version "$CURRENT_VERSION" --target-version "$TARGET_VERSION"; then
      display_message "$GREEN" "✅ Database updates completed successfully."
      log_info "Database updates completed successfully."
    else
      display_message "$RED" "❌ Database updates failed. Please check the logs."
      log_info "Database updates failed."
      return 1
    fi
  else
    display_message "$YELLOW" "⚠️ update.py not found. Skipping database updates."
    log_info "update.py not found. Skipping database updates."
  fi
}

# Function to display final instructions
function display_final_instructions() {
  display_message "$BLUE" "==============================================="
  display_message "$GREEN" "🎉 Hiddify Telegram Bot Update Complete!"
  display_message "$BLUE" "==============================================="
  display_message "$BLUE" "📁 Installation Directory: $INSTALL_DIR"
  display_message "$BLUE" "📝 Log File: $INSTALL_DIR/bot.log"
  display_message "$BLUE" "⚙️  To manage the bot, use the following commands:"
  display_message "$CYAN" "   cd $INSTALL_DIR && ./restart.sh     # Restart the bot"
  display_message "$CYAN" "   cd $INSTALL_DIR && ./update.sh      # Update the bot"
  display_message "$CYAN" "   tail -f $INSTALL_DIR/bot.log        # View bot logs"
  display_message "$YELLOW" "💬 Don't forget to send /start to your bot on Telegram!"
  display_message "$YELLOW" "💡 For support, contact: ${HIDY_BOT_ID}"
  display_message "$BLUE" "==============================================="
}

# Function to check if reinstallation is needed
function check_reinstall_needed() {
  display_message "$BLUE" "🔍 Checking if reinstallation is needed..."
  log_info "Checking if reinstallation is needed..."
  
  # Check if critical files exist
  local critical_files=("config.py" "hiddifyTelegramBot.py" "requirements.txt" "version.py")
  local missing_files=()
  
  for file in "${critical_files[@]}"; do
    if [ ! -f "$INSTALL_DIR/$file" ]; then
      missing_files+=("$file")
    fi
  done
  
  if [ ${#missing_files[@]} -gt 0 ]; then
    display_message "$YELLOW" "⚠️ Critical files are missing: ${missing_files[*]}"
    log_info "Critical files are missing: ${missing_files[*]}"
    
    # Ask for confirmation
    read -r -p "Do you want to reinstall the bot? [y/N] " response
    case "$response" in
      [yY][eE][sS]|[yY])
        display_message "$CYAN" "Reinstalling the bot..."
        log_info "User confirmed reinstallation."
        
        # Change to /opt directory
        cd /opt || display_error_and_exit "Failed to change directory to /opt"
        
        # Remove the old bot
        display_message "$CYAN" "Removing old bot directory..."
        log_info "Removing old bot directory..."
        rm -rf "$INSTALL_DIR"
        
        # Run the installation script
        display_message "$CYAN" "Running installation script..."
        log_info "Running installation script..."
        if bash -c "$(curl -Lfo- https://raw.githubusercontent.com/B3H1Z/Hiddify-Telegram-Bot/main/install.sh)"; then
          display_message "$GREEN" "✅ Bot has been reinstalled successfully."
          log_info "Bot has been reinstalled successfully."
          display_message "$GREEN" "Please run the bot configuration again."
          log_info "Please run the bot configuration again."
          exit 0
        else
          display_error_and_exit "Failed to reinstall the bot."
        fi
        ;;
      *)
        display_message "$YELLOW" "Bot has not been reinstalled. Exiting."
        log_info "User declined reinstallation. Exiting."
        exit 1
        ;;
    esac
  else
    display_message "$GREEN" "✅ All critical files are present. Proceeding with update."
    log_info "All critical files are present. Proceeding with update."
  fi
}

# Main execution
function main() {
  display_message "$BLUE" "==============================================="
  display_message "$GREEN" "🚀 Starting Hiddify Telegram Bot Update"
  display_message "$BLUE" "==============================================="
  log_info "==============================================="
  log_info "Starting Hiddify Telegram Bot Update"
  log_info "==============================================="
  
  # Step 1: Check prerequisites
  check_prerequisites
  
  # Step 2: Check if reinstallation is needed
  check_reinstall_needed
  
  # Step 3: Stop the bot gracefully
  stop_bot
  
  # Step 4: Wait for a few seconds
  display_message "$YELLOW" "⏳ Waiting for 5 seconds ..."
  log_info "Waiting for 5 seconds ..."
  sleep 5
  
  # Step 5: Get backup
  get_backup
  
  # Step 6: Update the bot
  update_bot
  
  # Step 7: Run database updates
  run_database_updates
  
  # Step 8: Restart the bot
  restart_bot
  
  # Step 9: Add cron jobs
  add_cron_jobs
  
  # Final instructions
  display_final_instructions
  
  log_info "Update completed successfully."
}

# Run the main function
main "$@"
