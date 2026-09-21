import 'dart:convert';

import 'package:app/config/api.dart';
import 'package:app/widgets/logout_button.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class CriarRelatorio extends StatefulWidget {
  final int pacienteId;
  final String pacienteNome;
  final String token;

  const CriarRelatorio({
    super.key,
    required this.pacienteId,
    required this.pacienteNome,
    required this.token,
  });

  @override
  State<CriarRelatorio> createState() => _CriarRelatoriosState();
}

class _CriarRelatoriosState extends State<CriarRelatorio> {
  final alimentacaoController = TextEditingController();
  final higieneController = TextEditingController();
  final pressaoController = TextEditingController();
  final glicemiaController = TextEditingController();
  final temperaturaController = TextEditingController();
  final observacoesController = TextEditingController();

  Future<void> criarRelatorio() async {
    final url = Uri.parse('$baseUrl/relatorios_diarios/criar');

    final dados = {
      'paciente_id': widget.pacienteId,
      'alimentacao': alimentacaoController.text.trim(),
      'pressao_arterial': pressaoController.text.trim(),
      'higiene': higieneController.text.trim(),
      'glicemia': glicemiaController.text.trim(),
      'temperatura': temperaturaController.text.trim(),
      'observacoes': observacoesController.text.trim(),
    };

    try {
      if (higieneController.text.trim().isEmpty) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: const Text('Informe a higiene.')));
        return;
      }

      if (observacoesController.text.trim().isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: const Text('Informe as observações.')),
        );
        return;
      }

      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer ${widget.token}',
          'Content-Type': 'application/json',
        },
        body: jsonEncode(dados),
      );

      if (response.statusCode == 201) {
        final resposta = jsonDecode(response.body);

        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              resposta['msg']?.toString() ?? 'Relatório criado com sucesso.',
            ),
          ),
        );

        alimentacaoController.clear();
        higieneController.clear();
        pressaoController.clear();
        glicemiaController.clear();
        temperaturaController.clear();
        observacoesController.clear();
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Registrar relatório do paciente: ${widget.pacienteNome}'),
        actions: [LogoutButton()],
      ),

      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 500),

              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      const Text(
                        'Criar relatório',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w600,
                        ),
                      ),

                      const SizedBox(height: 30),

                      TextField(
                        controller: alimentacaoController,
                        decoration: const InputDecoration(
                          labelText: 'Alimentação',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 30),

                      TextField(
                        controller: higieneController,
                        decoration: const InputDecoration(
                          labelText: 'Higiene',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 30),

                      TextField(
                        controller: pressaoController,
                        decoration: const InputDecoration(
                          labelText: 'Pressão arterial',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 30),

                      TextField(
                        controller: glicemiaController,
                        decoration: const InputDecoration(
                          labelText: 'Glicemia',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 30),

                      TextField(
                        controller: temperaturaController,
                        decoration: const InputDecoration(
                          labelText: 'Temperatura',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 30),

                      TextField(
                        controller: observacoesController,
                        maxLines: 3,
                        decoration: const InputDecoration(
                          labelText: 'Observações',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 30),

                      ElevatedButton(
                        onPressed: criarRelatorio,
                        child: const Text('Criar relatório'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
