import 'dart:convert';

import 'package:app/api.dart';
import 'package:app/logout_button.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class UsuariosDetalhes extends StatefulWidget {
  final Map usuario;
  final String token;

  const UsuariosDetalhes({
    super.key,
    required this.usuario,
    required this.token,
  });

  @override
  State<UsuariosDetalhes> createState() => _UsariosDetalhesState();
}

class _UsariosDetalhesState extends State<UsuariosDetalhes> {
  Map detalhes = {};

  @override
  void initState() {
    super.initState();
    buscarDetalhes();
  }

  Future<void> buscarDetalhes() async {
    if (widget.usuario['role'] == 'paciente') {
      final url = Uri.parse(
        '$baseUrl/pacientes/consultar/${widget.usuario['id']}',
      );
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
            detalhes = dados;
          });
        }
      } catch (erro) {
        debugPrint('erro: $erro');
      }
    } else if (widget.usuario['role'] == 'cuidador') {
      final url = Uri.parse(
        '$baseUrl/cuidadores/consultar/${widget.usuario['id']}',
      );

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
            detalhes = dados;
          });
        }
      } catch (erro) {
        debugPrint('erro: $erro');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Detalhes do usuário'),
        actions: [LogoutButton()],
      ),

      body: ListView(
        padding: EdgeInsets.all(20),
        children: [
          Text('ID: ${widget.usuario['id']}'),
          Text('Nome: ${widget.usuario['nome']}'),
          Text('E-mail: ${widget.usuario['email']}'),
          Text('Função: ${widget.usuario['role']}'),
          Text('Status: ${widget.usuario['status']}'),

          const SizedBox(height: 20),

          if (widget.usuario['role'] == 'paciente' &&
              detalhes['paciente'] != null) ...[
            Text('CPF: ${detalhes['paciente']['cpf'] ?? ''}'),
            Text('Nascimento: ${detalhes['paciente']['data_nascimento']}'),
            Text('Contato: ${detalhes['paciente']['tel']}'),
            Text('Endereço: ${detalhes['paciente']['endereco']}'),
          ],
          if (widget.usuario['role'] == 'cuidador' &&
              detalhes['cuidador'] != null) ...[
            Text('CPF: ${detalhes['cuidador']['cpf'] ?? ''}'),
            Text('Contato: ${detalhes['cuidador']['tel'] ?? ''}'),
            Text('Endereço: ${detalhes['cuidador']['endereco'] ?? ''}'),
          ],
        ],
      ),
    );
  }
}
