import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


#0. Зададим адреса файлов
items_p = 'items.csv'
orders_p = 'orders.csv'
users_p = 'users.csv'
paths = [items_p, orders_p, users_p]

# 1. Загрузка данных из файлов
@st.cache_data
def load_3files (paths):
    """
    Загрузка данных из трех csv файлов
    path1, path2, path3  - пути соответствующих файлов
    Функция возвращает кортеж из трех датафреймов
    """
    dfs = []
    for path in paths:
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f'Ошибка чтения файла {path}: {e}')
            df = pd.DataFrame() #Пустой датафрейм
        dfs.append(df)
    return tuple(dfs)


items, orders, users = load_3files(paths)

#Настроим страницу
st.set_page_config(
    page_title= 'Дашборд',
    layout= 'wide'
)

st.title('Анализ эффективности работы интернет-магазина')

# 2. Объединение таблиц

orders_users = orders.merge(
    users,
    on = 'user_id',
    how = 'left', 
    validate = 'm:1'
)

df_all = orders_users.merge(
    items, 
    on = 'item_id',
    how = 'left',
    validate = 'm:1'
)

# 3. Очистка данных
df_all.info()

#Числовые значения записаны в корректном типе, а вот даты -нет. 
# Исправим:

df_all['order_date'] = pd.to_datetime(df_all['order_date'], errors='coerce')
df_all['registration_date'] = pd.to_datetime(df_all['registration_date'], errors='coerce')

# Напишем функцию проверки пустых значений:


if df_all.isnull().sum().sum() != 0: 
    print(f'Найдены пропуски в данных: {df_all.isnull().sum()} . Вернитесь и исправьте')
    st.subheader('Найдены пропуски в данных. Для дальнейшего анализа необходимо их обработать')
    st.stop()

elif df_all.duplicated().sum() != 0:
    print(f'В датафрейме найдены дубликаты = {df_all.duplicated().sum()}. Вернитесь и исправьте')
    st.subheader('Найдены дубликаты строк. Для дальнейшего анализа необходимо их обработать')
    st.stop()
else:
    print ('Данные очищены и готовы к дальнейшему использованию')
    


# 4. Создание дашборда

# Зададим вкладки
tabs_names = ['Исходные данные', 'Ключевые показатели', 'Визуализация', 'Аналитические выводы']
original_data, metrics, visuals, conclusions = st.tabs(tabs_names)

# Выведем датафрейм с исходными данными:
with original_data:
    st.header('Исходные данные')
    st.dataframe(df_all)

# Добавим фильтры
# Сначала настроим сайдбар
    with st.sidebar:
        st.header ('Фильтры')
        date_filt= st.selectbox(
            label= 'Выберете дату заказа:',
            options= df_all['order_date'].dt.date.unique(),
            index= None
        )
        
        category_filt= st.selectbox(
            label= 'Выберете категорию товара:',
            options= df_all['category'].unique(),
            index= None
        )
        
    # Фильтрация
    if date_filt and category_filt:
        st.write(f'Отфильтрованные данные по дате {date_filt} и категории {category_filt}:')
        df_filtered = df_all[(df_all['order_date'].dt.date==date_filt)&(df_all['category']==category_filt)]
    elif date_filt:
        st.write(f'Отфильтрованные данные по дате {date_filt}:')
        df_filtered = df_all[df_all['order_date'].dt.date==date_filt]
    elif category_filt:
        st.write(f'Отфильтрованные данные по категории "{category_filt}":')
        df_filtered = df_all[df_all['category']==category_filt]
    else:
        st.write(f'Фильтры не выбраны')
        df_filtered = df_all

    st.dataframe(df_filtered)

    if df_filtered.empty:
        st.write('Недостаточно данных для дальнейшего анализа')
        st.stop()
    else:

# Расчитаем и выведем в новой вкладке статистики:

        with metrics:

            total_count_orders= df_filtered['order_id'].count()
            total_sales = (df_filtered['quantity']*df_filtered['price_per_unit']).sum()
            unique_users = df_filtered['user_id'].nunique()
            avg_check = 0 if total_count_orders==0 else total_sales/total_count_orders
        


            col1,col2 = st.columns([2,2])
            with col1:
                st.metric(label='Общее количество заказов', value=total_count_orders)
                st.metric (label= 'Общая выручка', value=total_sales)
            with col2:
                st.metric (label ='Количество уникальных пользователей' , value=unique_users)
                st.metric (label ='Средний чек' , value=avg_check)



        # Визуализация

        with visuals:

            fig,(ax1, ax2, ax3) = plt.subplots(3,1, figsize =(10,12))

            # Топ-10 товаров по выручке
            revenue_by_product= df_filtered.assign(revenue = df_filtered['quantity']
                                                *df_filtered['price_per_unit']).groupby(
                                                    'item_name')['revenue'].sum().reset_index()

            top_10=revenue_by_product.sort_values('revenue', ascending=False).head(10)
            
            # Горизонтальная столбчатая диаграмма 
            ax1.barh(top_10['item_name'], top_10['revenue'])
            ax1.set_title('Топ-10 товаров по выручке', loc = 'left')
            ax1.invert_yaxis()

            # Выручка по категориям товаров
            revenue_by_category = df_filtered.assign(revenue = df_filtered['quantity']
                                                *df_filtered['price_per_unit']).groupby(
                                                    'category')['revenue'].sum().reset_index().sort_values('revenue',ascending=False )

        
            #Круговая диаграмма
            if revenue_by_category['revenue'].sum() == 0:
                ax2.set_title('Нет данных для построения')
            else:
            
                ax2.pie (revenue_by_category['revenue'], autopct = '%1.1f%%', pctdistance = 0.85)
                ax2.set_title('Выручка по категориям товаров', loc = 'center')
                ax2.axis('equal')
                ax2.legend(
                    revenue_by_category['category'],
                    title='Категории товаров', 
                    loc ='center left',
                    )

            # Зависимость количества заказов от дня недели
            count_orders_by_day = df_filtered.groupby(df_filtered['order_date']
                                                    .dt.day_name(locale='ru_RU'))['order_id'].count().reset_index()
            days_ru = ['Понедельник', 'Вторник', 'Среда', 'Четверг' ,'Пятница' ,'Суббота', 'Воскресенье']
            count_orders_by_day['order_date']=pd.Categorical(count_orders_by_day['order_date'], 
                                                    categories= days_ru,
                                                    ordered=True)
            sorted_by_date  = count_orders_by_day.sort_values('order_date')
            # Линейный график
            ax3.plot(
                sorted_by_date['order_date'],
                sorted_by_date['order_id'],
                marker = 'o'
            )
            ax3.set_title('Зависимость количества заказов от дня недели')
            ax3.set_xlabel('День недели')
            ax3.set_ylabel('Количество заказов')

            plt.tight_layout()
            st.pyplot(fig)


        #Выводы
        with conclusions:
            st.write(f"Основываясь на данных, полученных в результате анализа можно сделать следующие выводы:\n"
                    f"1. За {(df_all['order_date'].max()-df_all['order_date'].min()).days+1} дней"
                    f"наблюдения было сделано {total_count_orders} заказов. \n"
                    f"2. При этом уникальных пользователей {unique_users}."
                    " Следовательно часть пользователей возвращается за повторными покупками.\n"
                    f"3. Основная выручка приходится на категорию: {revenue_by_category.iloc[0,0]}.\n"
                    f"4. Пик продаж приходится на {sorted_by_date.sort_values('order_id', ascending= False).iloc[0,0]}."
                    f" Так же видим на графике повышение количества продаж в"
                    f" {sorted_by_date.sort_values('order_id', ascending= False).iloc[1,0]} и "
                    f"{sorted_by_date.sort_values('order_id', ascending= False).iloc[2,0]}.\n"
                    )
            
             
