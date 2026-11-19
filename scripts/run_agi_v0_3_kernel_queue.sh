#!/bin/bash
cd /home/khjtony/workspace/wave_front/.claude/worktrees/bridge-cse_01RTpGKupSSHRF2WjPvHeBXq
LOG=reports/agi_v0_3_kernel_queue.log
echo "=== queue $(git rev-parse HEAD) limit ${WF_V03_MEMORY_GB:-23} GB $(date '+%F %T %Z')" >> $LOG
WF_V03_MEMORY_GB=${WF_V03_MEMORY_GB:-23} WF_V03_KERNEL_MINUTES=${WF_V03_KERNEL_MINUTES:-180} PYTHONPATH=. /home/khjtony/workspace/wave_front/.venv/bin/python scripts/agi_v0_3_kernel_queue.py >> $LOG 2>&1
echo "end $(date '+%F %T %Z')" >> $LOG
