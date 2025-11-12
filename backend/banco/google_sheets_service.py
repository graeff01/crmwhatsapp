"""
Google Sheets Integration Service
Sincronização automática e profissional do CRM com Google Sheets

Funcionalidades:
- Sincronização em tempo real de leads
- Registro automático de mensagens
- Dashboard de métricas
- Formatação profissional com cores e validação
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """
    Serviço profissional de integração com Google Sheets
    """
    
    # Configuração de cores profissionais
    COLORS = {
        'header': {'red': 0.26, 'green': 0.52, 'blue': 0.96},      # Azul
        'novo': {'red': 0.85, 'green': 0.92, 'blue': 0.83},        # Verde claro
        'contatado': {'red': 1.0, 'green': 0.95, 'blue': 0.80},    # Amarelo claro
        'negociacao': {'red': 0.98, 'green': 0.85, 'blue': 0.37},  # Amarelo
        'ganho': {'red': 0.72, 'green': 0.88, 'blue': 0.80},       # Verde
        'perdido': {'red': 0.96, 'green': 0.80, 'blue': 0.80}      # Vermelho claro
    }
    
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """
        Inicializa o serviço do Google Sheets
        
        Args:
            credentials_path: Caminho para arquivo JSON de credenciais
            spreadsheet_id: ID da planilha do Google Sheets
        """
        self.spreadsheet_id = spreadsheet_id
        
        # Escopos necessários
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        try:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=SCOPES
            )
            
            self.service = build('sheets', 'v4', credentials=credentials)
            self.sheets = self.service.spreadsheets()
            
            logger.info("✅ Google Sheets conectado com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar Google Sheets: {e}")
            raise
    
    # ========================================
    # SETUP INICIAL
    # ========================================
    
    def setup_spreadsheet(self) -> bool:
        """
        Configura a estrutura inicial da planilha
        Cria abas e headers formatados profissionalmente
        """
        try:
            logger.info("📊 Configurando estrutura da planilha...")
            
            # Criar abas
            self._create_sheets()
            
            # Configurar aba de Leads
            self._setup_leads_sheet()
            
            # Configurar aba de Mensagens
            self._setup_messages_sheet()
            
            # Configurar aba de Métricas
            self._setup_metrics_sheet()
            
            logger.info("✅ Planilha configurada com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar planilha: {e}")
            return False
    
    def _create_sheets(self):
        """Cria as abas necessárias"""
        try:
            # Obter abas existentes
            spreadsheet = self.sheets.get(spreadsheetId=self.spreadsheet_id).execute()
            existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            
            # Renomear primeira aba para "Leads"
            if 'Leads' not in existing_sheets:
                first_sheet_id = spreadsheet['sheets'][0]['properties']['sheetId']
                
                requests = [{
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': first_sheet_id,
                            'title': 'Leads'
                        },
                        'fields': 'title'
                    }
                }]
                
                self.sheets.batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': requests}
                ).execute()
            
            # Criar outras abas se não existirem
            sheets_to_create = ['Mensagens', 'Métricas']
            requests = []
            
            for sheet_name in sheets_to_create:
                if sheet_name not in existing_sheets:
                    requests.append({
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    })
            
            if requests:
                self.sheets.batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': requests}
                ).execute()
                
        except Exception as e:
            logger.error(f"Erro ao criar abas: {e}")
            raise
    
    def _setup_leads_sheet(self):
        """Configura aba de Leads com formatação profissional"""
        # Headers
        headers = [
            'ID', 'Nome', 'Telefone', 'Email', 'Status', 
            'Origem', 'Tags', 'SLA Status', 'Atendente',
            'Criado em', 'Atualizado em', 'Última Mensagem'
        ]
        
        # Escrever headers
        self.sheets.values().update(
            spreadsheetId=self.spreadsheet_id,
            range='Leads!A1:L1',
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()
        
        # Formatar headers
        self._format_header('Leads', 0, len(headers))
        
        # Congelar primeira linha
        self._freeze_rows('Leads', 1)
        
        # Ajustar largura das colunas
        self._auto_resize_columns('Leads', 0, len(headers))
        
        # Adicionar formatação extra (bordas, altura, zebrado)
        self._apply_professional_formatting('Leads', len(headers))
    
    def _setup_messages_sheet(self):
        """Configura aba de Mensagens"""
        headers = [
            'ID', 'Lead ID', 'Nome Lead', 'Direção', 
            'Mensagem', 'Data/Hora', 'Status'
        ]
        
        self.sheets.values().update(
            spreadsheetId=self.spreadsheet_id,
            range='Mensagens!A1:G1',
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()
        
        self._format_header('Mensagens', 0, len(headers))
        self._freeze_rows('Mensagens', 1)
        self._auto_resize_columns('Mensagens', 0, len(headers))
        
        # Adicionar formatação extra
        self._apply_professional_formatting('Mensagens', len(headers))
    
    def _setup_metrics_sheet(self):
        """Configura aba de Métricas com dashboard"""
        # Headers e estrutura
        data = [
            ['📊 DASHBOARD DE MÉTRICAS', '', ''],
            ['', '', ''],
            ['Métrica', 'Valor', 'Última Atualização'],
            ['Total de Leads', 0, datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Leads Novos', 0, datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Leads Contatados', 0, datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Leads em Negociação', 0, datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Leads Ganhos', 0, datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Leads Perdidos', 0, datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Taxa de Conversão (%)', 0, datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Tempo Médio de Resposta (min)', 0, datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]
        
        self.sheets.values().update(
            spreadsheetId=self.spreadsheet_id,
            range='Métricas!A1:C11',
            valueInputOption='USER_ENTERED',
            body={'values': data}
        ).execute()
        
        # Formatar título
        self._format_title('Métricas')
        
        # Formatar header da tabela
        self._format_header('Métricas', 2, 3)
        
        self._auto_resize_columns('Métricas', 0, 3)
    
    # ========================================
    # FORMATAÇÃO
    # ========================================
    
    def _format_header(self, sheet_name: str, row: int, num_cols: int):
        """Formata header com estilo profissional"""
        sheet_id = self._get_sheet_id(sheet_name)
        
        requests = [{
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': row,
                    'endRowIndex': row + 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': num_cols
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': self.COLORS['header'],
                        'textFormat': {
                            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
                            'fontSize': 11,
                            'bold': True
                        },
                        'horizontalAlignment': 'CENTER',
                        'verticalAlignment': 'MIDDLE'
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)'
            }
        }]
        
        self.sheets.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'requests': requests}
        ).execute()
    
    def _format_title(self, sheet_name: str):
        """Formata título do dashboard"""
        sheet_id = self._get_sheet_id(sheet_name)
        
        requests = [
            # Mesclar células do título
            {
                'mergeCells': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 3
                    },
                    'mergeType': 'MERGE_ALL'
                }
            },
            # Formatar título
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 3
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': self.COLORS['header'],
                            'textFormat': {
                                'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
                                'fontSize': 14,
                                'bold': True
                            },
                            'horizontalAlignment': 'CENTER',
                            'verticalAlignment': 'MIDDLE'
                        }
                    },
                    'fields': 'userEnteredFormat'
                }
            }
        ]
        
        self.sheets.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'requests': requests}
        ).execute()
    
    def _freeze_rows(self, sheet_name: str, num_rows: int):
        """Congela linhas superiores"""
        sheet_id = self._get_sheet_id(sheet_name)
        
        requests = [{
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {
                        'frozenRowCount': num_rows
                    }
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        }]
        
        self.sheets.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'requests': requests}
        ).execute()
    
    def _auto_resize_columns(self, sheet_name: str, start_col: int, end_col: int):
        """Ajusta largura das colunas automaticamente"""
        sheet_id = self._get_sheet_id(sheet_name)
        
        requests = [{
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': start_col,
                    'endIndex': end_col
                }
            }
        }]
        
        self.sheets.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'requests': requests}
        ).execute()
    
    def _apply_professional_formatting(self, sheet_name: str, num_cols: int):
        """Aplica formatação profissional: bordas, altura de linhas e zebrado"""
        sheet_id = self._get_sheet_id(sheet_name)
        
        requests = [
            # Aumentar altura da linha do header
            {
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'ROWS',
                        'startIndex': 0,
                        'endIndex': 1
                    },
                    'properties': {
                        'pixelSize': 35
                    },
                    'fields': 'pixelSize'
                }
            },
            # Altura padrão para linhas de dados (mais espaçadas)
            {
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'ROWS',
                        'startIndex': 1,
                        'endIndex': 1000  # Primeiras 1000 linhas
                    },
                    'properties': {
                        'pixelSize': 28
                    },
                    'fields': 'pixelSize'
                }
            },
            # Adicionar bordas em toda a área de dados
            {
                'updateBorders': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1000,
                        'startColumnIndex': 0,
                        'endColumnIndex': num_cols
                    },
                    'top': {
                        'style': 'SOLID',
                        'width': 1,
                        'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
                    },
                    'bottom': {
                        'style': 'SOLID',
                        'width': 1,
                        'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
                    },
                    'left': {
                        'style': 'SOLID',
                        'width': 1,
                        'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
                    },
                    'right': {
                        'style': 'SOLID',
                        'width': 1,
                        'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
                    },
                    'innerHorizontal': {
                        'style': 'SOLID',
                        'width': 1,
                        'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
                    },
                    'innerVertical': {
                        'style': 'SOLID',
                        'width': 1,
                        'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
                    }
                }
            },
            # Alinhamento vertical centralizado para todas as células
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 1,
                        'endRowIndex': 1000,
                        'startColumnIndex': 0,
                        'endColumnIndex': num_cols
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'verticalAlignment': 'MIDDLE',
                            'wrapStrategy': 'WRAP'
                        }
                    },
                    'fields': 'userEnteredFormat(verticalAlignment,wrapStrategy)'
                }
            },
            # Linhas zebradas (alternadas) - cor cinza claro
            {
                'addBanding': {
                    'bandedRange': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 1,
                            'endRowIndex': 1000,
                            'startColumnIndex': 0,
                            'endColumnIndex': num_cols
                        },
                        'rowProperties': {
                            'headerColor': {'red': 0.26, 'green': 0.52, 'blue': 0.96},
                            'firstBandColor': {'red': 1, 'green': 1, 'blue': 1},
                            'secondBandColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                        }
                    }
                }
            }
        ]
        
        self.sheets.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'requests': requests}
        ).execute()
    
    def _get_sheet_id(self, sheet_name: str) -> int:
        """Obtém ID da aba"""
        spreadsheet = self.sheets.get(spreadsheetId=self.spreadsheet_id).execute()
        
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        
        raise ValueError(f"Aba '{sheet_name}' não encontrada")
    
    # ========================================
    # SINCRONIZAÇÃO DE LEADS
    # ========================================
    
    def sync_lead(self, lead: Dict[str, Any]) -> bool:
        """
        Sincroniza um lead com a planilha
        Adiciona se não existir, atualiza se existir
        """
        try:
            # Verificar se lead já existe
            existing_row = self._find_lead_row(lead['id'])
            
            if existing_row:
                # Atualizar lead existente
                return self._update_lead(lead, existing_row)
            else:
                # Adicionar novo lead
                return self._add_lead(lead)
                
        except Exception as e:
            logger.error(f"❌ Erro ao sincronizar lead {lead.get('id')}: {e}")
            return False
    
    def _find_lead_row(self, lead_id: int) -> Optional[int]:
        """Encontra linha do lead na planilha"""
        try:
            result = self.sheets.values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Leads!A:A'
            ).execute()
            
            values = result.get('values', [])
            
            for idx, row in enumerate(values[1:], start=2):  # Pula header
                if row and str(row[0]) == str(lead_id):
                    return idx
            
            return None
            
        except Exception:
            return None
    
    def _add_lead(self, lead: Dict[str, Any]) -> bool:
        """Adiciona novo lead à planilha"""
        try:
            # Extrair tags se for lista de dicts
            tags_str = ''
            if lead.get('tags'):
                if isinstance(lead['tags'], list) and len(lead['tags']) > 0:
                    if isinstance(lead['tags'][0], dict):
                        tags_str = ', '.join([tag.get('name', '') for tag in lead['tags']])
                    else:
                        tags_str = ', '.join(lead['tags'])
            
            row_data = [
                lead.get('id', ''),
                lead.get('name', lead.get('nome', '')),  # Suporta ambos os campos
                lead.get('phone', lead.get('telefone', '')),  # Suporta ambos os campos
                lead.get('email', ''),
                lead.get('status', 'novo'),
                lead.get('source', lead.get('origem', '')),  # Suporta ambos os campos
                tags_str,
                lead.get('sla_status', ''),
                lead.get('vendedor_name', lead.get('atendente', '')),  # Suporta ambos os campos
                self._format_datetime(lead.get('created_at', lead.get('criado_em'))),
                self._format_datetime(lead.get('updated_at', lead.get('atualizado_em'))),
                self._format_datetime(lead.get('last_message', lead.get('ultima_mensagem')))
            ]
            
            self.sheets.values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Leads!A:L',
                valueInputOption='USER_ENTERED',
                body={'values': [row_data]}
            ).execute()
            
            logger.info(f"✅ Lead {lead['id']} adicionado à planilha")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar lead: {e}")
            return False
    
    def _update_lead(self, lead: Dict[str, Any], row: int) -> bool:
        """Atualiza lead existente"""
        try:
            # Extrair tags se for lista de dicts
            tags_str = ''
            if lead.get('tags'):
                if isinstance(lead['tags'], list) and len(lead['tags']) > 0:
                    if isinstance(lead['tags'][0], dict):
                        tags_str = ', '.join([tag.get('name', '') for tag in lead['tags']])
                    else:
                        tags_str = ', '.join(lead['tags'])
            
            row_data = [
                lead.get('id', ''),
                lead.get('name', lead.get('nome', '')),  # Suporta ambos os campos
                lead.get('phone', lead.get('telefone', '')),  # Suporta ambos os campos
                lead.get('email', ''),
                lead.get('status', 'novo'),
                lead.get('source', lead.get('origem', '')),  # Suporta ambos os campos
                tags_str,
                lead.get('sla_status', ''),
                lead.get('vendedor_name', lead.get('atendente', '')),  # Suporta ambos os campos
                self._format_datetime(lead.get('created_at', lead.get('criado_em'))),
                self._format_datetime(lead.get('updated_at', lead.get('atualizado_em'))),
                self._format_datetime(lead.get('last_message', lead.get('ultima_mensagem')))
            ]
            
            self.sheets.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'Leads!A{row}:L{row}',
                valueInputOption='USER_ENTERED',
                body={'values': [row_data]}
            ).execute()
            
            logger.info(f"✅ Lead {lead['id']} atualizado na planilha")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar lead: {e}")
            return False
    
    # ========================================
    # SINCRONIZAÇÃO DE MENSAGENS
    # ========================================
    
    def add_message(self, message: Dict[str, Any]) -> bool:
        """Adiciona mensagem à planilha"""
        try:
            row_data = [
                message.get('id', ''),
                message.get('lead_id', ''),
                message.get('lead_nome', ''),
                'Recebida' if message.get('is_from_me', False) == False else 'Enviada',
                message.get('mensagem', ''),
                self._format_datetime(message.get('timestamp')),
                message.get('status', '')
            ]
            
            self.sheets.values().append(
                spreadsheetId=self.spreadsheet_id,
                range='Mensagens!A:G',
                valueInputOption='USER_ENTERED',
                body={'values': [row_data]}
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar mensagem: {e}")
            return False
    
    # ========================================
    # MÉTRICAS
    # ========================================
    
    def update_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Atualiza métricas no dashboard"""
        try:
            timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
            
            rows_data = [
                ['Total de Leads', metrics.get('total_leads', 0), timestamp],
                ['Leads Novos', metrics.get('leads_novos', 0), timestamp],
                ['Leads Contatados', metrics.get('leads_contatados', 0), timestamp],
                ['Leads em Negociação', metrics.get('leads_negociacao', 0), timestamp],
                ['Leads Ganhos', metrics.get('leads_ganhos', 0), timestamp],
                ['Leads Perdidos', metrics.get('leads_perdidos', 0), timestamp],
                ['Taxa de Conversão (%)', metrics.get('taxa_conversao', 0), timestamp],
                ['Tempo Médio de Resposta (min)', metrics.get('tempo_medio_resposta', 0), timestamp],
            ]
            
            self.sheets.values().update(
                spreadsheetId=self.spreadsheet_id,
                range='Métricas!A4:C11',
                valueInputOption='USER_ENTERED',
                body={'values': rows_data}
            ).execute()
            
            logger.info("✅ Métricas atualizadas")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar métricas: {e}")
            return False
    
    # ========================================
    # UTILITÁRIOS
    # ========================================
    
    def _format_datetime(self, dt_string: Optional[str]) -> str:
        """Formata datetime para exibição"""
        if not dt_string:
            return ''
        
        try:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return dt_string
    
    def get_spreadsheet_url(self) -> str:
        """Retorna URL da planilha"""
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
    
    def test_connection(self) -> bool:
        """Testa conexão com a planilha"""
        try:
            self.sheets.get(spreadsheetId=self.spreadsheet_id).execute()
            logger.info("✅ Conexão com Google Sheets OK!")
            return True
        except Exception as e:
            logger.error(f"❌ Erro na conexão: {e}")
            return False