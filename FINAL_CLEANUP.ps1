$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$paths = @(
  '.perfume_frontend_backup',
  '.perfume_frontend_backup_v2',
  '.perfume_frontend_phase01_backup',
  '.perfume_frontend_phase02_backup',
  '.perfume_frontend_phase03_final_backup',
  '.perfume_frontend_phase04_backup',
  '.perfume_frontend_phase06_backup',
  '.perfume_frontend_phase07_backup',
  '.perfume_frontend_phase07_v2_backup',
  '.perfume_frontend_phase08_backup',
  '.perfume_frontend_phase09_backup',
  '.perfume_frontend_phase10_backup',
  '.perfume_frontend_phase11_backup',
  '.restore_core_frontend_backup',
  '.task-core',
  'CODEX_TASK.md',
  'implement_task.py',
  'implement_task_templates.py',
  'prepare_task_changes.py',
  'task-care-tests.log',
  'task-first-tests.log',
  'phase_01_home_auth.py',
  'phase_02_unify_frontend.py',
  'phase_03_final_auth_slider.py',
  'phase_04_professional_pages.py',
  'phase_05_perfume_shop_rebuild.py',
  'phase_06_theme_tracking_fix.py',
  'phase_07_owner_login_daymode.py',
  'phase_07_owner_login_daymode_v2.py',
  'phase_08_account_support_layout_fix.py',
  'phase_09_owner_admin_visual_studio.py',
  'phase_10_owner_access_edit_profile.py',
  'phase_11_owner_console_perfume_polish.py',
  'phase_11_perfume_admin_polish.py',
  'rebuild_perfume_frontend.py',
  'restore_core_frontend_keep_home.py',
  'upgrade_perfume_frontend_v2.py'
)

foreach ($path in $paths) {
  $target = Join-Path $root $path
  if (Test-Path $target) {
    Remove-Item $target -Recurse -Force
    Write-Host "Removed $path"
  }
}

Get-ChildItem -Path $root -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host 'Legacy backups/scripts cleaned. Run: git add -A'
