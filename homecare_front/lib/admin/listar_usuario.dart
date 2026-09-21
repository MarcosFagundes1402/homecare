import 'dart:convert';

import 'package:app/config/api.dart';
import 'package:app/widgets/logout_button.dart';
import 'package:app/admin/usuarios_detalhes.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ListarUsuarios extends StatefulWidget {
  final String token;

  const ListarUsuarios({super.key, required this.token});

  @override
  State<ListarUsuarios> createState() => _ListarUsuariosState();
}

class _ListarUsuariosState extends State<ListarUsuarios> {
  List usuarios = [];
  String msg = '';
  String traduzirRole(String role) {
    switch (role) {
      case 'admin':
        return 'Administrador';
      case 'cuidador':
        return 'Cuidador';
      case 'paciente':
        return 'Paciente';
      default:
        return role;
    }
  }

  @override
  void initState() {
    super.initState();
    buscarUsuarios();
  }

  Future<void> buscarUsuarios() async {
    final url = Uri.parse('$baseUrl/usuarios/consultar');

    try {
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer ${widget.token}',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final dados = jsonDecode(response.body);

        if (!mounted) return;

        setState(() {
          usuarios = List.from(dados);
        });
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Lista de todos os pacientes'),
        actions: [LogoutButton()],
      ),

      body: usuarios.isEmpty
          ? const Center(child: Text('Nenhum usuário encontrado'))
          : ListView.builder(
              itemCount: usuarios.length,
              itemBuilder: (context, index) {
                final usuario = usuarios[index];

                return ListTile(
                  title: Text(
                    usuario['nome'],
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(
                    'ID: ${usuario['id']} • ${usuario['email']} • Função: ${traduzirRole(usuario['role'])}',
                  ),
                  trailing: Text(usuario['status']),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => UsuariosDetalhes(
                          usuario: usuario,
                          token: widget.token,
                        ),
                      ),
                    );
                  },
                );
              },
            ),
    );
  }
}
