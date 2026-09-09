import 'package:flutter/material.dart';
import 'package:app/paciente_home.dart';
import 'package:app/cuidador_home.dart';
class HomeScreen extends StatelessWidget {
  final String nome;
  final String role;
  final String token;

  const HomeScreen({
    super.key,
    required this.nome,
    required this.role,
    required this.token,
  });

  @override
  Widget build(BuildContext context) {
    switch (role.toLowerCase()) {
      case 'paciente':
        return PacienteHome(nome: nome, token: token);

      case 'cuidador':
        return CuidadorHome(nome: nome, token: token);

      case 'admin':
        return Scaffold(body: Center(child: Text('Área do admin - $nome')));

      default:
        return const Scaffold(
          body: Center(child: Text('Perfil não encontrado.')),
        );
    }
  }
}
