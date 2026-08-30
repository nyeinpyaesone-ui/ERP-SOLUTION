# Enterprise ERP Solution - Required Secrets Configuration
# =========================================================
# 
# This document outlines the required GitHub repository secrets for the
# ERP-SOLUTION CI/CD pipeline. These secrets must be configured in your
# GitHub repository settings before the workflows can run successfully.
#
# Configuration Steps:
# 1. Go to your GitHub repository: nyeinpyaesone-ui/ERP-SOLUTION
# 2. Navigate to Settings > Secrets and variables > Actions
# 3. Click "New repository secret" for each secret below
#
# -----------------------------------------------------------------------------
# REQUIRED SECRETS (Must be configured)
# -----------------------------------------------------------------------------

# Docker Hub Authentication
# --------------------------
# Used for pushing Docker images to Docker Hub registry
# 
# Secret Name: DOCKERHUB_USERNAME
# Value: Your Docker Hub username (e.g., "nyeinpyaesone-ui")
# Description: Docker Hub account username for image push operations
#
# Secret Name: DOCKERHUB_PASSWORD
# Value: Your Docker Hub password or access token
# Description: Docker Hub password or personal access token with write permissions
# Note: For better security, use a Docker Hub access token instead of your password
#       Generate token at: https://hub.docker.com/settings/security

# GitHub API Access (for advanced workflow operations)
# -----------------------------------------------------
# Used for GitHub API interactions in deployment workflows
#
# Secret Name: API_GITHUB_USERNAME
# Value: Your GitHub username (e.g., "nyeinpyaesone-ui")
# Description: GitHub username for API authentication
#
# Secret Name: API_GITHUB_KEY
# Value: GitHub Personal Access Token (Classic) or Fine-grained PAT
# Description: GitHub API token with repo and workflow permissions
# Note: Generate token at: https://github.com/settings/tokens
#       Required scopes: repo, workflow, read:org


# -----------------------------------------------------------------------------
# OPTIONAL SECRETS (Recommended for enhanced features)
# -----------------------------------------------------------------------------

# Code Coverage Reporting
# ------------------------
# Used for uploading test coverage reports to Codecov
#
# Secret Name: CODECOV_TOKEN
# Value: Your Codecov repository upload token
# Description: Token for uploading coverage reports to codecov.io
# Note: Get token from: https://app.codecov.io/account/[your-org]/[your-repo]
#       If not set, coverage reports will be generated but not uploaded

# Testcontainers Cloud Integration
# ---------------------------------
# Used for enhanced containerized testing with Testcontainers Cloud
#
# Secret Name: TC_CLOUD_TOKEN
# Value: Your Testcontainers Cloud API token
# Description: Token for Testcontainers Cloud service
# Note: Get token from: https://cloud.testcontainers.com/
#       If not set, tests will run locally without TC Cloud

# Slack Notifications (Optional)
# -------------------------------
# Used for sending build/deployment notifications to Slack
#
# Secret Name: SLACK_WEBHOOK_URL
# Value: Slack Incoming Webhook URL
# Description: Webhook URL for posting messages to Slack channel
# Note: Create webhook at: https://api.slack.com/messaging/webhooks


# -----------------------------------------------------------------------------
# ENVIRONMENT CONFIGURATION
# -----------------------------------------------------------------------------
# 
# In addition to secrets, configure the following environment in GitHub:
#
# Environment Name: Docker
# Protection Rules: (Optional) Require reviewers for production deployments
# Deployment Branches: develop (for dev builds), main (for production)
#
# To configure:
# 1. Go to Settings > Environments
# 2. Click "New environment"
# 3. Name it "Docker"
# 4. Configure branch protection rules as needed


# -----------------------------------------------------------------------------
# SECURITY BEST PRACTICES
# -----------------------------------------------------------------------------
#
# 1. Use Personal Access Tokens instead of passwords where possible
# 2. Rotate tokens regularly (every 90 days recommended)
# 3. Use fine-grained PATs with minimum required permissions
# 4. Never commit secrets to the repository
# 5. Use environment-specific secrets for staging/production separation
# 6. Audit secret access regularly in GitHub Settings
# 7. Enable secret scanning in repository settings


# -----------------------------------------------------------------------------
# VERIFICATION STEPS
# -----------------------------------------------------------------------------
#
# After configuring secrets, verify they work correctly:
#
# 1. Push a test commit to the develop branch
# 2. Check Actions tab for workflow execution
# 3. Verify all jobs complete successfully
# 4. Check Docker Hub for pushed image with tag "develop-latest"
# 5. Review artifacts (SBOM, coverage reports, deployment summary)
#
# Troubleshooting:
# - If login fails: Verify DOCKERHUB_USERNAME and DOCKERHUB_PASSWORD
# - If push fails: Ensure token has write permissions
# - If tests fail: Check CODECOV_TOKEN (optional) or review test logs


# -----------------------------------------------------------------------------
# EXAMPLE SECRET CONFIGURATION SUMMARY
# -----------------------------------------------------------------------------
#
# | Secret Name          | Required | Example Value              |
# |---------------------|----------|----------------------------|
# | DOCKERHUB_USERNAME  | ✅ Yes   | nyeinpyaesone-ui           |
# | DOCKERHUB_PASSWORD  | ✅ Yes   | dckr_pat_xxxxxxxxxxxx      |
# | API_GITHUB_USERNAME | ✅ Yes   | nyeinpyaesone-ui           |
# | API_GITHUB_KEY      | ✅ Yes   | github_pat_xxxxxxxxxxxx    |
# | CODECOV_TOKEN       | ⚠️ No    | xxxxxxxx-xxxx-xxxx-...     |
# | TC_CLOUD_TOKEN      | ⚠️ No    | tc_cloud_xxxxxxxxxxxx      |
# | SLACK_WEBHOOK_URL   | ⚠️ No    | https://hooks.slack.com/.. |
#
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# IMPORTANT NOTES
# -----------------------------------------------------------------------------
#
# 📌 You have already set up the required secrets!
# 
# Next Steps:
# 1. Configure Repository Variables (see VARIABLES_SETUP.md)
#    - DOCKER_REGISTRY_URL: Your registry URL (e.g., https://hub.docker.com)
#    - DEPLOYMENT_ENV_NAME: (Optional) Custom environment name
#    - REGISTRY_TYPE: (Optional) Type of registry (dockerhub, ghcr, etc.)
#
# 2. Set up the "Docker" Environment
#    - Go to Settings > Environments
#    - Create environment named "Docker"
#    - Optionally add deployment branch rules
#
# 3. Test the Workflow
#    - Push a commit to the develop branch
#    - Monitor the Actions tab
#    - Verify image is pushed to your registry
#
# -----------------------------------------------------------------------------
