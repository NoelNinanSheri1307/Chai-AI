import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/theme_provider.dart';

class ThemeToggleButton extends StatelessWidget {
  const ThemeToggleButton({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    final currentMode = themeProvider.themeMode;

    IconData icon;

    if (currentMode == ThemeMode.dark) {
      icon = Icons.dark_mode;
    } else if (currentMode == ThemeMode.light) {
      icon = Icons.light_mode;
    } else {
      icon = Icons.settings_brightness;
    }

    return IconButton(
      tooltip: "Toggle Theme",
      icon: Icon(icon),
      onPressed: () {
        if (currentMode == ThemeMode.dark) {
          themeProvider.setTheme(ThemeMode.light);
        } else {
          themeProvider.setTheme(ThemeMode.dark);
        }
      },
      onLongPress: () {
        themeProvider.setTheme(ThemeMode.system);
      },
    );
  }
}
