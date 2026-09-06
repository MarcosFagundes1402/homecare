import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {

  final String nome;
  final String role;

  const HomeScreen({
    super.key,
    required this.nome,
    required this.role,
  });
  
  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('Home Care'),
      ),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Bem-vindo, $nome',
              style: const TextStyle(
                fontSize: 25,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 10),

            Text('Perfil: $role')
          ],
        ),
      ),
    );
  }
}