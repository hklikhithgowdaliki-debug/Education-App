import 'package:flutter/material.dart';

import 'src/catalog_service.dart';
import 'src/download_service.dart';
import 'src/screens.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const EduPapersApp());
}

class EduPapersApp extends StatelessWidget {
  const EduPapersApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Karnataka Question Papers',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1565C0)),
        useMaterial3: true,
      ),
      home: HomeShell(catalog: CatalogService(), downloads: DownloadService()),
    );
  }
}
