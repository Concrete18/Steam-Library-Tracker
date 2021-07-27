from openpyxl.styles.borders import Side
import openpyxl, os, shutil
from time import sleep


class Indexer:

    script_dir = os.path.dirname(os.path.abspath(__file__))
    changes_made = 0


    def __init__(self, excel_filename, workbook_name, column_name, column_letter):
        '''
        Class object init.
        '''
        self.excel_filename = excel_filename
        self.file_path = os.path.join(os.getcwd(), excel_filename + '.xlsx')
        self.wb = openpyxl.load_workbook(self.file_path)
        self.cur_workbook = self.wb[workbook_name]
        self.column_name = column_name
        self.column_letter = column_letter
        # column and row indexes
        self.column_i = self.create_column_index()
        self.row_i = self.create_row_index(self.column_name)


    def create_column_index(self):
        '''
        Creates the column index.
        '''
        column_i = {}
        for i in range(1, len(self.cur_workbook['1'])+1):
            title = self.cur_workbook.cell(row=1, column=i).value
            if title is not None:
                column_i[title] = i
        return column_i


    def create_row_index(self, column_name):
        '''
        Creates the row index.
        '''
        row_i = {}
        for i in range(1, len(self.cur_workbook[self.column_letter])):
            title = self.cur_workbook.cell(row=i+1, column=self.column_i[column_name]).value
            if title is not None:
                row_i[title] = i+1
        return row_i


    def format_cells(self, game_name, do_not_center_list=[], do_not_border_list=[]):
        '''
        Aligns specific columns to center and adds border to cells.
        '''
        align = openpyxl.styles.alignment.Alignment(
            horizontal='center', vertical='center', text_rotation=0, wrap_text=False, shrink_to_fit=True, indent=0)
        border = openpyxl.styles.borders.Border(
            left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'),
            diagonal=None, outline=True, start=None, end=None)
        for cell in self.column_i.keys():
            if cell not in do_not_center_list:
                self.cur_workbook.cell(row=self.row_i[game_name], column=self.column_i[cell]).alignment = align
            if cell not in do_not_border_list:
                self.cur_workbook.cell(row=self.row_i[game_name], column=self.column_i[cell]).border = border
        # TODO add decimal point setting
        # cell.number_format = "0.0000" # 4 decimal places


    def get_cell(self, row_value, column_value):
        '''
        Gets the cell value based on the row and column
        '''
        if type(row_value) == str:
            value = str(self.cur_workbook.cell(row=self.row_i[row_value], column=self.column_i[column_value]).value)
            return value
        else:
            value = str(self.cur_workbook.cell(row=row_value, column=self.column_i[column_value]).value)
            return value


    def update_cell(self, row_value, column_value, string):
        '''
        Updates the given cell based on row and column to the given value.
        if row_value is not a string, it will be considered an exact index instead.
        '''
        if type(row_value) == str:
            self.cur_workbook.cell(row=self.row_i[row_value], column=self.column_i[column_value]).value = string
        else:
            self.cur_workbook.cell(row=row_value, column=self.column_i[column_value]).value = string
        self.changes_made = 1


    def add_new_cell(self, cell_dict):
        '''
        Adds the given dictionary onto a new line within the excel sheet.
        If dictionary keys match existing columns within the set sheet, it will add the value to that column.
        '''
        append_list = []
        for column in self.column_i:
            if column in cell_dict:
                append_list.append(cell_dict[column])
            else:
                append_list.append('')
                print(f'Missing data for {column}.')
        self.cur_workbook.append(append_list)
        self.changes_made = 1


    def save_excel_sheet(self):
        '''
        Backs up the excel file before saving the changes.
        It will keep trying to save until it completes in case of permission errors caused by the file being open.
        '''
        try:
            # backups the file before saving.
            shutil.copy(self.file_path, os.path.join(self.script_dir, self.excel_filename + '.bak'))
            # saves the file once it is closed
            print('\nSaving...')
            first_run = 1
            while True:
                try:
                    self.wb.save(self.excel_filename + '.xlsx')
                    print('Save Complete.                                  ')
                    break
                except PermissionError:
                    if first_run:
                        print('Make sure the excel sheet is closed.', end='\r')
                        first_run = 0
                    sleep(.1)
        except KeyboardInterrupt:
            print('\nCancelling Save')
            exit()
