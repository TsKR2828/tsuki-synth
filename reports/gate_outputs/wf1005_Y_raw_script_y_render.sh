#!/bin/bash
Y=E:/Tsuki-project/_scratch/wf1005/Y
cd /e/Tsuki-project/_scratch/wf1005/Y
for s in scores/*.score.json; do
  b=$(basename $s .score.json)
  ./bin/TsukiSynthCLI_current.exe $s --output render_cur > render_cur/$b.log 2>&1; rc1=$?
  ./bin/TsukiSynthCLI_9123db8f_build20260915.exe $s --output render_arch > render_arch/$b.log 2>&1; rc2=$?
  echo "$b rc_cur=$rc1 rc_arch=$rc2"
done
