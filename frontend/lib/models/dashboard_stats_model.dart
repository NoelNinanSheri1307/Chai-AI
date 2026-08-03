// lib/models/dashboard_stats_model.dart

class DashboardStats {
  final int totalScans;
  final int lowRisk;
  final int mediumRisk;
  final int highRisk;

  DashboardStats({
    required this.totalScans,
    required this.lowRisk,
    required this.mediumRisk,
    required this.highRisk,
  });
}
