import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class CriarMedicamentos extends StatefulWidget {
  final String token;

  const CriarMedicamentos({super.key, required this.token});

  @override
  State<CriarMedicamentos> createState() => _CriarMedicamentosState();
}

class _CriarMedicamentosState extends State<CriarMedicamentos> {
  List pacientes = [];
  int? pacienteSelecionado;

  final nomeController = TextEditingController();
  final dosagemController = TextEditingController();
  final frequenciaController = TextEditingController();
  final horarioController = TextEditingController();
  final obsController = TextEditingController();

  @override
  void initState() {
    super.initState();
    buscarPacientes();
  }

  Future<void> buscarPacientes() async {
    final url = Uri.parse('http://localhost:5000/pacientes/consultar');

    try {
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer ${widget.token}',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final dados = jsonDecode(response.body);

        if (!mounted) return;

        setState(() {
          pacientes = List.from(dados)
              .where((paciente) => paciente['status'] == 'ativo')
              .toList();
        });
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  Future<void> enviarMedicamentos() async {
    final url = Uri.parse('http://localhost:5000/medicamentos/criar');

    final dados = {
      'paciente_id': pacienteSelecionado,
      'nome': nomeController.text.trim(),
      'dosagem': dosagemController.text.trim(),
      'frequencia': frequenciaController.text.trim(),
      'horario': horarioController.text.trim(),
      'obs': obsController.text.trim(),
    };

    try {
      if (pacienteSelecionado == null) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Selecione um paciente.')));
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

      if (response.statusCode == 200 || response.statusCode == 201) {
        setState(() {
          pacienteSelecionado = null;
        });

        nomeController.clear();
        dosagemController.clear();
        frequenciaController.clear();
        horarioController.clear();
        obsController.clear();

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              resposta['msg']?.toString() ?? 'Medicamento criado com sucesso.',
            ),
          ),
        );
      } else if (response.statusCode == 409) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${resposta['erro']}\n${resposta['sugestao']}'),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              resposta['erro']?.toString() ?? 'Erro ao criar medicamento.',
            ),
          ),
        );
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Criar medicamentos')),
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
                        'Criar medicamento',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w600,
                        ),
                      ),

                      const SizedBox(height: 20),

                      TextField(
                        controller: nomeController,
                        decoration: const InputDecoration(
                          labelText: 'Nome do medicamento',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 20),

                      TextField(
                        controller: dosagemController,
                        decoration: const InputDecoration(
                          labelText: 'Dosagem',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 20),

                      TextField(
                        controller: frequenciaController,
                        decoration: const InputDecoration(
                          labelText: 'Frequencia',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 20),

                      TextField(
                        controller: horarioController,
                        decoration: const InputDecoration(
                          labelText: 'Horário',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 20),

                      TextField(
                        controller: obsController,
                        decoration: const InputDecoration(
                          labelText: 'Observações',
                          border: OutlineInputBorder(),
                        ),
                      ),

                      const SizedBox(height: 20),

                      DropdownButtonFormField<int>(
                        initialValue: pacienteSelecionado,
                        decoration: const InputDecoration(
                          labelText: 'Selecione o paciente',
                          border: OutlineInputBorder(),
                        ),
                        items: pacientes.map<DropdownMenuItem<int>>((paciente) {
                          return DropdownMenuItem<int>(
                            value: paciente['id'],
                            child: Text(
                              '${paciente['nome']} - ID: ${paciente['id']}',
                            ),
                          );
                        }).toList(),
                        onChanged: (value) {
                          pacienteSelecionado = value;
                        },
                      ),

                      const SizedBox(height: 20),

                      ElevatedButton(
                        onPressed: () {
                          enviarMedicamentos();
                        },
                        child: const Text('Criar medicamento'),
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

  @override
  void dispose() {
    nomeController.dispose();
    dosagemController.dispose();
    frequenciaController.dispose();
    horarioController.dispose();
    obsController.dispose();
    super.dispose();
  }
}
