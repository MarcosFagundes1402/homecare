import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class CriarVinculosScreen extends StatefulWidget {
  final String token;

  const CriarVinculosScreen({super.key, required this.token});

  @override
  State<CriarVinculosScreen> createState() => _CriarVinculosScreenState();
}

class _CriarVinculosScreenState extends State<CriarVinculosScreen> {
  List cuidadores = [];
  List pacientes = [];
  int? cuidadorSelecionado;
  int? pacienteSelecionado;
  Map? vinculoCriado;

  @override
  void initState() {
    super.initState();
    buscarCuidadores();
    buscarPacientes();
  }

  Future<void> buscarCuidadores() async {
    final url = Uri.parse('http://localhost:5000/cuidadores/consultar');

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
          cuidadores = List.from(dados)
              .where((cuidador) => cuidador['status'] == 'ativo')
              .toList();
        });
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
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

      if (response.statusCode == 200) {
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

  Future<void> criarVinculo() async {
    if (cuidadorSelecionado == null || pacienteSelecionado == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: const Text('Selecione um cuidador e um paciente.')),
      );
      return;
    }

    final url = Uri.parse(
      'http://localhost:5000//cuidadores_pacientes/criar-vinculo',
    );

    try {
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer ${widget.token}',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'cuidador_id': cuidadorSelecionado,
          'paciente_id': pacienteSelecionado,
        }),
      );

      final dados = jsonDecode(response.body);

      if (!mounted) return;

      if (response.statusCode == 200 || response.statusCode == 201) {
        final cuidador = cuidadores.firstWhere(
          (c) => c['id'] == cuidadorSelecionado,
        );

        final paciente = pacientes.firstWhere(
          (c) => c['id'] == pacienteSelecionado,
        );

        setState(() {
          vinculoCriado = {
            'cuidador': cuidador,
            'paciente': paciente,
          };
        });
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(dados['erro'] ?? 'Erro ao criar vínculo.')),
        );
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Criar vínculos')),
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
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      const Text(
                        'Novo vínculo',
                        style: TextStyle(
                          fontSize: 30,
                          fontWeight: FontWeight.w600,
                        ),
                      ),

                      const SizedBox(height: 20),

                      DropdownButtonFormField<int>(
                        decoration: const InputDecoration(
                          labelText: 'Selecione um cuidador',
                          border: OutlineInputBorder(),
                        ),
                        items: cuidadores.map<DropdownMenuItem<int>>((
                          cuidador,
                        ) {
                          return DropdownMenuItem<int>(
                            value: cuidador['id'],
                            child: Text(
                              '${cuidador['nome']} - ID: ${cuidador['id']}',
                            ),
                          );
                        }).toList(),
                        onChanged: (value) {
                          cuidadorSelecionado = value;
                        },
                      ),

                      const SizedBox(height: 20),

                      DropdownButtonFormField<int>(
                        decoration: const InputDecoration(
                          labelText: 'Selecione um paciente',
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

                      SizedBox(
                        width: 150,
                        child: ElevatedButton(
                          onPressed: criarVinculo,
                          child: const Text('Criar vínculo'),
                        ),
                      ),

                      if (vinculoCriado != null) ...[
                        const SizedBox(height: 20),

                        Center(
                          child: ConstrainedBox(
                            constraints: const BoxConstraints(maxWidth:  500),
                            child: Card(
                              child: Padding(
                                padding: const EdgeInsetsGeometry.all(20),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text(
                                      'Vinculo criado!',
                                      style: TextStyle(
                                        fontSize: 22,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),

                                    const SizedBox(height: 15),

                                    Text('Cuidador: ${vinculoCriado!['cuidador']['nome']} | ID: ${vinculoCriado!['cuidador']['id']}'),

                                    Text('Paciente: ${vinculoCriado!['paciente']['nome']} | ID: ${vinculoCriado!['paciente']['id']}'),

                                  ],
                                ),
                              ),
                            ),
                          ),
                        )
                      ]
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
