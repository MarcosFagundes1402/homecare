import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'minhas_administracoes.dart';

class PacienteHome extends StatefulWidget {
  final String nome;
  final String token;

  const PacienteHome({super.key, required this.nome, required this.token});

  @override
  State<PacienteHome> createState() => _PacienteHomeState();
}

class _PacienteHomeState extends State<PacienteHome> {
  List cuidadores = [];
  List medicamentos = [];

  @override
  void initState() {
    super.initState();

    buscarCuidadores();
    buscarMedicamentos();
  }

  // FAZ REQUISIÇÃO NA API E VERIFICA QUAL CUIDADOR ESTA VINCULADO AO PACIENTE
  Future<void> buscarCuidadores() async {
    final url = Uri.parse(
      'http://localhost:5000/cuidadores_pacientes/meus-cuidadores',
    );

    try {
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer ${widget.token}',
          'Contente-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final dados = jsonDecode(response.body);

        if (!mounted) return;

        setState(() {
          cuidadores = dados;
        });
      }
    } catch (erro) {
      debugPrint('ERRO: $erro');
    }
  }

  // FAZ A REQUISIÇÃO NA API E RETORNA OS MEDICAMENTOS DO PACIENTE
  Future<void> buscarMedicamentos() async {
    final url = Uri.parse(
      'http://localhost:5000/medicamentos/meus-medicamentos',
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
          medicamentos = dados['medicamentos'];
        });
      }
    } catch (erro) {
      debugPrint('ERRO MEDICAMENTOS: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    final cuidadoresVisiveis = cuidadores.take(2).toList();
    final medicamentosVisiveis = medicamentos.take(3).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Home Paciente')),

      // CARD DE BEM-VINDO
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Center(
            child: Text(
              'Bem-vindo, ${widget.nome}',
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
            ),
          ),

          const SizedBox(height: 50),

          // CARD MEUS CUIDADORES
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 500),

              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      const Text(
                        'Meus cuidadores',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w600,
                        ),
                      ),

                      const SizedBox(height: 10),

                      ...cuidadoresVisiveis.map((cuidador) {
                        return ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text('Nome: ${cuidador['nome']}'),
                          subtitle: Text('Contato: ${cuidador['tel']}'),
                          trailing: const Icon(Icons.arrow_forward_ios),
                          onTap: () {
                            //detalhes depois
                          },
                        );
                      }),

                      if (cuidadores.length > 2)
                        TextButton(
                          onPressed: () {},
                          child: const Text('Ver mais...'),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          // CARD MEUS MEDICAMENTOS
          const SizedBox(height: 50),

          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 500),

              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      const Text(
                        'Meus medicamentos',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),

                      const SizedBox(height: 10),

                      ...medicamentosVisiveis.map((medicamento) {
                        return ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(medicamento['nome']),
                          subtitle: Text(
                            'Dosagem: ${medicamento['dosagem']} | Horário: ${medicamento['horario']}',
                          ),

                          trailing: const Icon(Icons.arrow_forward_ios),
                          onTap: () {},
                        );
                      }),

                      if (medicamentosVisiveis.length > 2)
                        TextButton(
                          onPressed: () {},
                          child: const Text('Ver mais...'),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          const SizedBox(height: 50),

          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 500),
              child: Card(
                child: ListTile(
                  title: const Text('Meu histórico de administrações'),
                  trailing: const Icon(Icons.arrow_forward_ios),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => MinhasAdministracoes(
                          nome: widget.nome,
                          token: widget.token,
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
