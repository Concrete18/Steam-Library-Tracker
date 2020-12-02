def Create_Column_Row_Index(workbook=None, column_name=None, column_letter='B'):
    column_index = Column_Index(workbook)
    row_index = Row_Index(workbook, column_name, column_letter)
    return column_index, row_index


def Column_Index(workbook):
    '''
    Creates excel sheet index based on column names such as Anime name and Score.
    The starting_row var is the number of the row that the main column is on.
    '''
    column_index = {}
    for i in range(1, len(workbook['1'])+1):
        title = workbook.cell(row=1, column=i).value
        if title is not None:
            column_index[title] = i
    return column_index


def Row_Index(workbook, column_name, column_letter):
    '''
    Creates excel sheet index based on anime names.
    The starting_col var is the number of the column that the main column is on.
    '''
    column_index = Column_Index(workbook, )
    row_index = {}
    for i in range(1, len(workbook[column_letter])):
        title = workbook.cell(row=i+1, column=column_index[column_name]).value
        if title is not None:
            row_index[title] = i+1
    return row_index
