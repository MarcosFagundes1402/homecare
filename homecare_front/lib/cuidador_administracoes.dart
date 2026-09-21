import 'dart:convert';

import 'package:app/api.dart';
import 'package:app/logout_button.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class CuidadorAdministracoes extends StatefulWidget {
  final String pacienteNome;
  final int pacienteId;
  final String token;

  final bool modoAdmin;

  const CuidadorAdministracoes({
    super.key,
    required this.pacienteNome,
    required this.pacienteId,
    required this.token,
    this.modoAdmin = false,
  });

  @override
  State<CuidadorAdministracoes> createState() => _CuidadorAdministracoesState();
}

class _CuidadorAdministracoesState extends State<CuidadorAdministracoes> {
  List administracoes = [];
  String msg = "";

  @override
  void initState() {
    super.initState();
    buscarAdministracoes();
  }

  Future<void> buscarAdministracoes() async {
    final url = Uri.parse(
      widget.modoAdmin
          ? '$baseUrl/administracao_medicamentos/admin/paciente/${widget.pacienteId}'
          : '$baseUrl/administracao_medicamentos/cuidador/paciente/${widget.pacienteId}',
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
        final lista = dados['administracoes'] ?? [];

        if (!mounted) return;

        if (lista.isEmpty) {
          setState(() {
            msg = dados['msg'] ?? 'Nenhum histórico encontrado.';
          });
        } else {
          setState(() {
            administracoes = lista;
            msg = '';
          });
        }
      }
    } catch (erro) {
      debugPrint('Status: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Administrações de : ${widget.pacienteNome}'),
        actions: [LogoutButton()],
      ),

      body: administracoes.isEmpty
          ? Center(child: Text(msg))
          : ListView.builder(
              padding: const EdgeInsets.all(20),
              itemCount: administracoes.length,
              itemBuilder: (context, index) {
                final administracao = administracoes[index];

                return Card(
                  child: ExpansionTile(
                    title: Text(administracao['medicamento']['nome']),

                    subtitle: Text(
                      'Administrado por: ${administracao['responsavel']['nome']}'
                      ' em: ${administracao['horario_administrado']}',
                    ),

                    children: [
                      Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Text(
                              'Dosagem administrada: ${administracao['dosagem_administrada']}',
                            ),

                            Text('Status: ${administracao['status']}'),

                            Text('Observação: ${administracao['obs']}'),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),

      // criar a rota no back para poder fazer essa consulta
    );
  }
}
