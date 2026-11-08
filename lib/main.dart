import 'package:flutter/material.dart';

void main() => runApp(const SideStartApp());

class SideStartApp extends StatelessWidget {
  const SideStartApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SideStart',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF63E6CB),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF10181D),
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _count = 0;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('SideStart'),
        backgroundColor: Colors.transparent,
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Icon(
                      Icons.auto_awesome_rounded,
                      color: colors.primary,
                      size: 48,
                    ),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Ein kleiner Anfang.',
                    style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Deine erste App ist da. Probier sie aus.',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                  const SizedBox(height: 32),
                  Card(
                    margin: EdgeInsets.zero,
                    child: Padding(
                      padding: const EdgeInsets.all(28),
                      child: Column(
                        children: [
                          const Text('DEIN ZÄHLER'),
                          const SizedBox(height: 12),
                          Semantics(
                            liveRegion: true,
                            label: 'Zählerstand',
                            child: Text(
                              '$_count',
                              key: const ValueKey('counter-value'),
                              style: Theme.of(context)
                                  .textTheme
                                  .displayLarge
                                  ?.copyWith(color: colors.primary),
                            ),
                          ),
                          const SizedBox(height: 24),
                          FilledButton.icon(
                            key: const ValueKey('increment-button'),
                            onPressed: () => setState(() => _count++),
                            icon: const Icon(Icons.add_rounded),
                            label: const Text('Eins dazu'),
                          ),
                          const SizedBox(height: 8),
                          TextButton(
                            key: const ValueKey('reset-button'),
                            onPressed: _count == 0
                                ? null
                                : () => setState(() => _count = 0),
                            child: const Text('Zurücksetzen'),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Ganz ohne Konto. Ganz bei dir.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
