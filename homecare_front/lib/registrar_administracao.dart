import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class RegistrarAdministracao extends StatefulWidget {
  final int pacienteId;
  final String pacienteNome;
  final String token;

  const RegistrarAdministracao({
    super.key,
    required this.pacienteId,
    required this.pacienteNome,
    required this.token,
  });

  @override
  State<RegistrarAdministracao> createState() => _RegistrarAdministracaoState();
}

class _RegistrarAdministracaoState extends State<RegistrarAdministracao> {
  List medicamentos = [];
  String msg = '';
  int? medicamentoSelecionado;

  final dosagemController = TextEditingController();
  final obsController = TextEditingController();

  @override
  void initState() {
    super.initState();
    buscarMedicamentos();
  }

  Future<void> buscarMedicamentos() async {
    final url = Uri.parse(
      'http://localhost:5000/medicamentos/consultar-paciente/${widget.pacienteId}',
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
        final lista = dados['medicamentos'] ?? [];

        if (!mounted) return;

        setState(() {
          medicamentos = lista;
          msg = lista.isEmpty
              ? dados['msg'] ??
                    'Este paciente não possui medicamentos para registrar.'
              : '';
        });
      }

      debugPrint('Status: ${response.statusCode}');
      debugPrint('body: ${response.body}');
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  Future<void> registrarAdministracao() async {
    final url = Uri.parse(
      'http://localhost:5000/administracao_medicamentos/criar',
    );

    final dados = {
      'medicamento_id': medicamentoSelecionado,
      'paciente_id': widget.pacienteId,
      'dosagem_administrada': dosagemController.text.trim(),
      'obs': obsController.text.trim(),
      'status': 'ativo',
    };

    try {
      if (medicamentoSelecionado == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Selecione um medicamento.')),
        );
        return;
      }

      if (dosagemController.text.trim().isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Informe a dosagem administrada.')),
        );
        return;
      }

      if (obsController.text.trim().isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Informe uma observação.')),
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

      final resposta = jsonDecode(response.body);

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            resposta['msg']?.toString() ??
                'Administração registrada com sucesso.',
          ),
        ),
      );

      setState(() {
        medicamentoSelecionado = null;
      });

      dosagemController.clear();
      obsController.clear();
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Registrar Administração do paciente: ${widget.pacienteNome}',
        ),
      ),

      body: medicamentos.isEmpty
          ? Center(
              child: Text(
                msg.isEmpty ? 'Carregando...' : msg,
                textAlign: TextAlign.center,
              ),
            )
          : Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  DropdownButtonFormField<int>(
                    initialValue: medicamentoSelecionado,

                    decoration: const InputDecoration(
                      labelText: 'medicamento',
                      border: OutlineInputBorder(),
                    ),

                    items: medicamentos.map<DropdownMenuItem<int>>((
                      medicamento,
                    ) {
                      return DropdownMenuItem<int>(
                        value: medicamento['id'],
                        child: Text(medicamento['nome']),
                      );
                    }).toList(),

                    onChanged: (valor) {
                      setState(() {
                        medicamentoSelecionado = valor;
                      });
                    },
                  ),

                  const SizedBox(height: 20),

                  TextField(
                    controller: dosagemController,
                    decoration: const InputDecoration(
                      labelText: 'Dosagem administrada',
                      border: OutlineInputBorder(),
                    ),
                  ),

                  const SizedBox(height: 20),

                  TextField(
                    controller: obsController,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      labelText: 'Observação',
                      border: OutlineInputBorder(),
                    ),
                  ),

                  const SizedBox(height: 20),

                  ElevatedButton(
                    onPressed: registrarAdministracao,
                    child: const Text('Registrar administração'),
                  ),
                ],
              ),
            ),
    );
  }
}
