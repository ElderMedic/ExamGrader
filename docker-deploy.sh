#!/bin/bash
# Quick deployment script for ExamGrader

set -e

echo "=== ExamGrader Docker Deployment ==="

# Build Docker image
echo "Building Docker image..."
docker build -t exam-grader:latest .

echo ""
echo "=== Usage Examples ==="
echo ""
echo "1. Single capture and grade:"
echo "   docker run --rm -v \$(pwd)/screenshots:/app/screenshots \\"
echo "     -e VLLM_API_BASE=http://host.docker.internal:8000/v1 \\"
echo "     exam-grader:latest python main.py --mode single"
echo ""
echo "2. Periodic grading:"
echo "   docker run --rm -v \$(pwd)/screenshots:/app/screenshots \\"
echo "     -e VLLM_API_BASE=http://host.docker.internal:8000/v1 \\"
echo "     exam-grader:latest python main.py --mode periodic --interval 5 --duration 30"
echo ""
echo "3. With reference answer:"
echo "   docker run --rm -v \$(pwd)/screenshots:/app/screenshots \\"
echo "     -v \$(pwd)/examples:/app/examples \\"
echo "     -e VLLM_API_BASE=http://host.docker.internal:8000/v1 \\"
echo "     exam-grader:latest python main.py --mode single \\"
echo "     --reference-answer examples/reference_answer.md"
echo ""
echo "4. Using docker-compose:"
echo "   docker-compose run --rm exam-grader python main.py --mode single"
echo ""
echo "=== Note ==="
echo "Make sure vLLM server is running on host at port 8000"
echo "For Linux, you may need to modify docker-compose.yml to use host network"
