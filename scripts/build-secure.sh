#!/bin/bash

# ======================================================================================
# SECURE DOCKER BUILD SCRIPT FOR WARREN BOT
# ======================================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
readonly IMAGE_NAME="warren-bot"
readonly BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
readonly VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
readonly VERSION=$(grep '^version = ' "$PROJECT_DIR/pyproject.toml" | sed 's/version = "\(.*\)"/\1/')

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Security: Verify required files exist
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    local required_files=(
        "pyproject.toml"
        "poetry.lock"
        "src/warren_bot/__init__.py"
        "Dockerfile"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$PROJECT_DIR/$file" ]]; then
            echo -e "${RED}❌ Required file missing: $file${NC}"
            exit 1
        fi
    done
    
    # Security: Check for sensitive files that shouldn't be in build context
    local sensitive_patterns=(
        ".env"
        "*.key"
        "*.pem"
        "*password*"
        "*secret*"
    )
    
    for pattern in "${sensitive_patterns[@]}"; do
        if find "$PROJECT_DIR" -maxdepth 2 -name "$pattern" | grep -q .; then
            echo -e "${YELLOW}⚠️  Warning: Potential sensitive files found matching '$pattern'${NC}"
            echo -e "${YELLOW}   Please ensure these are properly excluded in .dockerignore${NC}"
        fi
    done
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Security: Scan for vulnerabilities in dependencies
security_scan() {
    echo -e "${BLUE}🔒 Running security scans...${NC}"
    
    # Check if safety is available for Python dependency scanning
    if command -v safety >/dev/null 2>&1; then
        echo -e "${BLUE}📦 Scanning Python dependencies...${NC}"
        cd "$PROJECT_DIR"
        if safety check --json --output /tmp/safety-report.json 2>/dev/null; then
            echo -e "${GREEN}✅ No known vulnerabilities in Python dependencies${NC}"
        else
            echo -e "${YELLOW}⚠️  Found potential vulnerabilities. Check /tmp/safety-report.json${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Safety not installed. Consider running: pip install safety${NC}"
    fi
    
    # Check Docker daemon security
    if command -v docker >/dev/null 2>&1; then
        local docker_version
        docker_version=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown")
        echo -e "${BLUE}🐳 Docker version: $docker_version${NC}"
    fi
}

# Build the secure Docker image
build_image() {
    echo -e "${BLUE}🏗️  Building secure Warren Bot image...${NC}"
    echo "Image: $IMAGE_NAME:$VERSION"
    echo "Build Date: $BUILD_DATE"
    echo "VCS Ref: $VCS_REF"
    
    cd "$PROJECT_DIR"
    
    # Security: Build with specific build arguments and security options
    docker build \
        --build-arg WARREN_VERSION="$VERSION" \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg VCS_REF="$VCS_REF" \
        --tag "$IMAGE_NAME:latest" \
        --tag "$IMAGE_NAME:$VERSION" \
        --tag "$IMAGE_NAME:secure" \
        --label "build.date=$BUILD_DATE" \
        --label "build.version=$VERSION" \
        --label "build.vcs-ref=$VCS_REF" \
        --label "security.scan-required=true" \
        --progress=plain \
        .
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Build completed successfully${NC}"
    else
        echo -e "${RED}❌ Build failed${NC}"
        exit 1
    fi
}

# Security: Test the built image
test_image() {
    echo -e "${BLUE}🧪 Testing built image...${NC}"
    
    # Test 1: Basic import test
    echo -e "${BLUE}📋 Testing Python imports...${NC}"
    if docker run --rm --read-only "$IMAGE_NAME:latest" python -c "import warren_bot; print('✅ Import test passed')"; then
        echo -e "${GREEN}✅ Import test passed${NC}"
    else
        echo -e "${RED}❌ Import test failed${NC}"
        exit 1
    fi
    
    # Test 2: Security test - verify running as non-root
    echo -e "${BLUE}🔒 Testing non-root execution...${NC}"
    local user_id
    user_id=$(docker run --rm --read-only "$IMAGE_NAME:latest" id -u)
    if [[ "$user_id" != "0" ]]; then
        echo -e "${GREEN}✅ Running as non-root user (UID: $user_id)${NC}"
    else
        echo -e "${RED}❌ Container running as root - security risk!${NC}"
        exit 1
    fi
    
    # Test 3: File system permissions
    echo -e "${BLUE}📁 Testing filesystem permissions...${NC}"
    docker run --rm --read-only --tmpfs /tmp --tmpfs /app/logs "$IMAGE_NAME:latest" \
        python -c "
import os
import tempfile
# Test temp directory is writable
with tempfile.NamedTemporaryFile(dir='/tmp') as f:
    f.write(b'test')
print('✅ Temporary filesystem test passed')
" && echo -e "${GREEN}✅ Filesystem permissions test passed${NC}"
    
    # Test 4: Health check
    echo -e "${BLUE}❤️  Testing health check...${NC}"
    docker run --rm --read-only "$IMAGE_NAME:latest" \
        python -c "import warren_bot; import sys; sys.exit(0)" && \
        echo -e "${GREEN}✅ Health check test passed${NC}"
}

# Security: Scan the built image for vulnerabilities
image_security_scan() {
    echo -e "${BLUE}🔍 Scanning image for security vulnerabilities...${NC}"
    
    # Use Docker Scout if available
    if docker scout version >/dev/null 2>&1; then
        echo -e "${BLUE}🕵️  Running Docker Scout scan...${NC}"
        docker scout cves "$IMAGE_NAME:latest" || echo -e "${YELLOW}⚠️  Docker Scout scan completed with warnings${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker Scout not available. Consider enabling for vulnerability scanning.${NC}"
    fi
    
    # Use Grype if available
    if command -v grype >/dev/null 2>&1; then
        echo -e "${BLUE}🔍 Running Grype vulnerability scan...${NC}"
        grype "$IMAGE_NAME:latest" -o table || echo -e "${YELLOW}⚠️  Grype scan completed with findings${NC}"
    else
        echo -e "${YELLOW}⚠️  Grype not installed. Consider installing for vulnerability scanning.${NC}"
    fi
    
    # Basic image inspection
    echo -e "${BLUE}📊 Image inspection...${NC}"
    docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # Security: Check image layers
    echo -e "${BLUE}🔍 Analyzing image layers...${NC}"
    docker history --no-trunc "$IMAGE_NAME:latest" | head -10
}

# Generate security report
generate_security_report() {
    local report_file="/tmp/warren-bot-security-report.txt"
    echo -e "${BLUE}📄 Generating security report...${NC}"
    
    {
        echo "Warren Bot Security Build Report"
        echo "=================================="
        echo "Build Date: $BUILD_DATE"
        echo "Version: $VERSION"
        echo "VCS Ref: $VCS_REF"
        echo ""
        echo "Image Details:"
        docker inspect "$IMAGE_NAME:latest" --format='
Image ID: {{.Id}}
Created: {{.Created}}
Size: {{.Size}} bytes
Architecture: {{.Architecture}}
OS: {{.Os}}
User: {{.Config.User}}
WorkingDir: {{.Config.WorkingDir}}
'
        echo ""
        echo "Security Labels:"
        docker inspect "$IMAGE_NAME:latest" --format='{{range $key, $value := .Config.Labels}}{{$key}}={{$value}}{{"\n"}}{{end}}' | grep -E "(security|build|org\.opencontainers)"
        
    } > "$report_file"
    
    echo -e "${GREEN}✅ Security report generated: $report_file${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}🚀 Starting secure Warren Bot build process${NC}"
    echo "========================================================"
    
    check_prerequisites
    security_scan
    build_image
    test_image
    image_security_scan
    generate_security_report
    
    echo ""
    echo -e "${GREEN}🎉 Secure build completed successfully!${NC}"
    echo "========================================================"
    echo "Available images:"
    docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    echo ""
    echo "To run securely:"
    echo "  docker-compose -f docker-compose.secure.yml up -d"
    echo ""
    echo "Security recommendations:"
    echo "  • Always run with --read-only flag"
    echo "  • Use secrets management for sensitive data"
    echo "  • Regularly update base images"
    echo "  • Monitor for security vulnerabilities"
    echo "  • Implement proper logging and monitoring"
}

# Execute main function
main "$@"