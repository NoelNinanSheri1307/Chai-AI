import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../views/dashboard/main_dashboard.dart';
import '../../providers/auth_provider.dart';
import '../auth/login_screen.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);

    if (authProvider.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    if (authProvider.isAuthenticated) {
      return const MainDashboard();
    } else {
      return const LoginScreen();
    }
  }
}
