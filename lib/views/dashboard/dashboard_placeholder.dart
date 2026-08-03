import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/theme_toggle_button.dart';

class DashboardPlaceholder extends StatelessWidget {
  const DashboardPlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text("Dashboard"),
        actions: [
          const ThemeToggleButton(),
          IconButton(
            onPressed: () {
              authProvider.logout();
            },
            icon: const Icon(Icons.logout),
          ),
        ],
      ),

      body: Center(child: Text("Welcome ${authProvider.user?.name}")),
    );
  }
}
