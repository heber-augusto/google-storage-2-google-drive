import os
import pandas as pd
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient.discovery import build

google_storage_json_filename = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
google_drive_json_filename = os.getenv('GD_JSON_FILE', '')

# Cliente do Google Cloud Storage
storage_client = storage.Client.from_service_account_json(google_storage_json_filename)
bucket_id = os.getenv('GCP_BUCKET', '')

gs_prefix = os.getenv('GCP_PREFIX', '')
dest_folder_id = os.getenv('DEST_FOLDER_ID', '')
team_drive_id = os.getenv('TEAM_DRIVER_ID', '')

# Acesse o bucket desejado
blobs = storage_client.list_blobs(
        bucket_or_name = bucket_id,
        prefix = gs_prefix)
gs_files = [blob for blob in blobs]

gs_files_list = [\
  {
      'current_path': gs_file.name.replace(f"{gs_prefix}/", ''),
      'size': int(gs_file.size)
  } \
  for gs_file in gs_files if gs_file.size > 0]

print(f"{gs_prefix} : {sum([file['size'] for file in gs_files_list])} bytes")




def autenticar_servico(json_caminho, escopos):
    credenciais = service_account.Credentials.from_service_account_file(json_caminho, scopes=escopos)
    return build('drive', 'v3', credentials=credenciais)

def obter_dados_pasta(servico, team_drive_id, pasta_id, current_path=''):
    quantidade_arquivos = 0
    tamanho_total = 0
    lista_arquivos = []
    pagina_token = None

    while True:
        # Listar os arquivos na pasta
        resultados = servico.files().list(
            q=f"'{pasta_id}' in parents",
            fields="*",
            driveId=team_drive_id,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            corpora='drive',
            pageToken=pagina_token
            ).execute()
        arquivos = resultados.get('files', [])


        for arquivo in arquivos:
            if (arquivo['mimeType'] != 'application/vnd.google-apps.folder'):
                if int(arquivo['quotaBytesUsed']) > 0:
                    tamanho_total += int(arquivo['size'])
                    quantidade_arquivos += 1
                    arquivo['current_path'] = f"{current_path}{arquivo['name']}"
                    lista_arquivos.append(arquivo)
            else:
                quantidade_arquivos_temp, tamanho_total_temp, lista_arquivos_temp = obter_dados_pasta(
                    servico,
                    team_drive_id,
                    arquivo['id'],
                    current_path = f"{current_path}{arquivo['name']}/")
                quantidade_arquivos += quantidade_arquivos_temp
                tamanho_total += tamanho_total_temp
                lista_arquivos.extend(lista_arquivos_temp)

        # Verificar se há mais páginas
        pagina_token = resultados.get('nextPageToken')
        if not pagina_token:
            break

    return quantidade_arquivos, tamanho_total, lista_arquivos


# Escopos necessários para acessar a API do Google Drive
escopos = ['https://www.googleapis.com/auth/drive.readonly']

# Autenticar o serviço
gd_service = autenticar_servico(google_drive_json_filename, escopos)

# Obter dados da pasta no Team Drive
quantidade_arquivos, tamanho_total, lista_arquivos = obter_dados_pasta(gd_service, team_drive_id, dest_folder_id)

# Exibir resultados
print(f'Quantidade de arquivos na pasta: {quantidade_arquivos}')
print(f'Tamanho total ocupado: {tamanho_total} bytes')

gd_files_list = [\
 {
     'current_path': gd_file['current_path'],
     'size': int(gd_file['size'])
 } \
 for gd_file in lista_arquivos if gd_file['trashed'] == False]


try:
    gd_files_df = pd.DataFrame.from_dict(gd_files_list)
    gd_files_df.columns = ['current_path', 'gd_size']
except KeyError:
    gd_files_df = pd.DataFrame(columns = ['current_path', 'gd_size'])
gs_files_df = pd.DataFrame.from_dict(gs_files_list)
gs_files_df.columns = ['current_path', 'gs_size']

# perform a full outer join on the customer_id column
all_files = pd.merge(
    gd_files_df, 
    gs_files_df, 
    on='current_path', 
    how='outer')

dif_files = all_files[(all_files.gd_size != all_files.gs_size)]

gd_to_delete = dif_files[dif_files.gs_size.isna()]
gs_to_copy = dif_files[dif_files.gd_size.isna()]
print(dif_files)
print(gd_to_delete)
print(gs_to_copy)


