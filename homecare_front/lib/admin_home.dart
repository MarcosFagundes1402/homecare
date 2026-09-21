import 'package:app/consultar_administra%C3%A7%C3%B5es.dart';
import 'package:app/consultar_madicamentos.dart';
import 'package:app/consultar_medicamento_individual.dart';
import 'package:app/consultar_relatorio.dart';
import 'package:app/criar_medicamentos.dart';
import 'package:app/criar_usuarios.dart';
import 'package:app/criar_vinculos_screen.dart';
import 'package:app/listar_usuario.dart';
import 'package:app/vinculos_screen.dart';
import 'package:flutter/material.dart';

class AdminHome extends StatefulWidget {
  final String nome;
  final String token;

  const AdminHome({super.key, required this.nome, required this.token});

  @override
  State<AdminHome> createState() => _AdminHomeState();
}

class _AdminHomeState extends State<AdminHome> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Área do Administrador')),

      body: ListView(
        padding: const EdgeInsets.all(50),
        children: [
          Center(
            child: Text(
              'Bem-vindo, ${widget.nome}',
              style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w600),
            ),
          ),

          // CARD DE USUARIOS
          const SizedBox(height: 40),

          Card(
            child: ExpansionTile(
              title: const Text(
                'Usuários',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
              ),
              children: [
                ListTile(
                  title: const Text('Listar usuários'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            ListarUsuarios(token: widget.token),
                      ),
                    );
                  },
                ),

                ListTile(
                  title: const Text('Criar usuário'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            CriarUsuarios(token: widget.token),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),

          // CARD DE VINCULOS
          Card(
            child: ExpansionTile(
              title: const Text(
                'Vínculos',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
              ),
              children: [
                ListTile(
                  title: const Text('Criar vínculo'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            CriarVinculosScreen(token: widget.token),
                      ),
                    );
                  },
                ),

                ListTile(
                  title: const Text('Ver vínculos'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            VinculosScreen(token: widget.token),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),

          //CARD DE MEDICAMENTOS
          Card(
            child: ExpansionTile(
              title: const Text(
                'Medicamentos',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
              ),

              children: [
                ListTile(
                  title: const Text('Consultar todos os medicamentos'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            ConsultarMadicamentos(token: widget.token),
                      ),
                    );
                  },
                ),

                ListTile(
                  title: const Text('Consultar por paciente'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            ConsultarMedicamentoIndividual(token: widget.token),
                      ),
                    );
                  },
                ),

                ListTile(
                  title: const Text('Criar medicamento'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            CriarMedicamentos(token: widget.token),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),

          //CARD ADMINISTRACOES
          Card(
            child: ExpansionTile(
              title: const Text(
                'Administrações',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
              ),
              children: [
                ListTile(
                  title: const Text('Consultar histórico'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            ConsultarAdministracoes(token: widget.token),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),

          //CARD RELATORIOS
          Card(
            child: ExpansionTile(
              title: const Text(
                'Relatórios',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
              ),
              children: [
                ListTile(
                  title: const Text('Consultar histórico'),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ConsultarRelatorio(
                          token: widget.token
                        )
                        ,
                      )
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
