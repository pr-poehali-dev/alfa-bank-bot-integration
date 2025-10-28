import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

const API_URL = 'https://functions.poehali.dev/5c16926a-4625-421c-a828-127ea6ceccef';

interface UserData {
  id?: number;
  telegram_id: number;
  username?: string;
  first_name?: string;
  promo_code: string;
  balance: number;
}

interface StatsData {
  total_referrals: number;
  cards_issued: number;
}

interface Transaction {
  id: number;
  amount: number;
  type: string;
  description: string;
  created_at: string;
}

const Index = () => {
  const [user, setUser] = useState<UserData | null>(null);
  const [stats, setStats] = useState<StatsData>({ total_referrals: 0, cards_issued: 0 });
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [copySuccess, setCopySuccess] = useState(false);
  const { toast } = useToast();

  const mockTelegramId = 111222333;

  useEffect(() => {
    initUser();
  }, []);

  const initUser = async () => {
    try {
      const registerResponse = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'register',
          telegram_id: mockTelegramId,
          username: 'demo_user',
          first_name: 'Демо'
        })
      });

      if (!registerResponse.ok) throw new Error('Failed to register');
      
      const statsResponse = await fetch(`${API_URL}?telegram_id=${mockTelegramId}`);
      if (!statsResponse.ok) throw new Error('Failed to fetch stats');
      
      const data = await statsResponse.json();
      setUser(data.user);
      setStats(data.stats);
      setTransactions(data.transactions || []);
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось загрузить данные',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const copyPromoCode = () => {
    if (user?.promo_code) {
      navigator.clipboard.writeText(user.promo_code);
      setCopySuccess(true);
      toast({
        title: 'Скопировано!',
        description: 'Промокод скопирован в буфер обмена'
      });
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  const sharePromoCode = () => {
    const text = `🎁 Оформи карту Альфа-Банка по моему промокоду ${user?.promo_code} и получи бонусы!`;
    const url = `https://t.me/share/url?url=${encodeURIComponent(window.location.href)}&text=${encodeURIComponent(text)}`;
    window.open(url, '_blank');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-alfa-red via-red-600 to-red-700 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-white"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-alfa-red via-red-600 to-red-700 pb-6">
      <div className="container max-w-2xl mx-auto px-4 py-6">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center justify-center gap-2">
            <Icon name="CreditCard" size={32} className="text-white" />
            Альфа-Банк
          </h1>
          <p className="text-white/90 text-sm">Реферальная программа</p>
        </div>

        <Tabs defaultValue="home" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6 bg-white/10 backdrop-blur-sm">
            <TabsTrigger value="home" className="data-[state=active]:bg-white data-[state=active]:text-alfa-red">
              <Icon name="Home" size={18} className="mr-2" />
              Главная
            </TabsTrigger>
            <TabsTrigger value="referrals" className="data-[state=active]:bg-white data-[state=active]:text-alfa-red">
              <Icon name="Users" size={18} className="mr-2" />
              Рефералы
            </TabsTrigger>
            <TabsTrigger value="history" className="data-[state=active]:bg-white data-[state=active]:text-alfa-red">
              <Icon name="Receipt" size={18} className="mr-2" />
              История
            </TabsTrigger>
          </TabsList>

          <TabsContent value="home" className="space-y-4">
            <Card className="bg-white p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm text-gray-500">Ваш баланс</p>
                  <p className="text-4xl font-bold text-alfa-red">{user?.balance.toFixed(2)} ₽</p>
                </div>
                <div className="bg-alfa-red/10 p-4 rounded-full">
                  <Icon name="Wallet" size={32} className="text-alfa-red" />
                </div>
              </div>
              <Button className="w-full bg-alfa-red hover:bg-red-700 text-white">
                <Icon name="Download" size={18} className="mr-2" />
                Вывести средства
              </Button>
            </Card>

            <Card className="bg-white p-6 shadow-xl">
              <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
                <Icon name="Gift" size={20} className="text-alfa-red" />
                Ваш промокод
              </h3>
              <div className="bg-gray-100 p-4 rounded-lg mb-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500 mb-1">Промокод для друзей</p>
                  <p className="text-2xl font-bold text-alfa-red tracking-wider">{user?.promo_code}</p>
                </div>
                <Button
                  onClick={copyPromoCode}
                  variant="outline"
                  size="icon"
                  className={`${copySuccess ? 'bg-green-100 border-green-500' : ''}`}
                >
                  <Icon name={copySuccess ? "Check" : "Copy"} size={18} />
                </Button>
              </div>
              <Button onClick={sharePromoCode} className="w-full bg-blue-500 hover:bg-blue-600 text-white">
                <Icon name="Share2" size={18} className="mr-2" />
                Поделиться в Telegram
              </Button>
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-700">
                  💰 <strong>200₽</strong> за каждого друга, который оформит карту по вашему промокоду
                </p>
              </div>
            </Card>

            <Card className="bg-white p-6 shadow-xl">
              <h3 className="font-bold text-lg mb-4">О карте</h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <Icon name="CreditCard" size={20} className="text-alfa-red mt-1" />
                  <div>
                    <p className="font-semibold">Кэшбэк до 10%</p>
                    <p className="text-sm text-gray-600">На все покупки</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Icon name="Shield" size={20} className="text-alfa-red mt-1" />
                  <div>
                    <p className="font-semibold">Бесплатное обслуживание</p>
                    <p className="text-sm text-gray-600">При условиях</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Icon name="Zap" size={20} className="text-alfa-red mt-1" />
                  <div>
                    <p className="font-semibold">Моментальный выпуск</p>
                    <p className="text-sm text-gray-600">Онлайн за 5 минут</p>
                  </div>
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="referrals" className="space-y-4">
            <Card className="bg-white p-6 shadow-xl">
              <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                <Icon name="Users" size={20} className="text-alfa-red" />
                Статистика рефералов
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <p className="text-3xl font-bold text-alfa-red">{stats.total_referrals}</p>
                  <p className="text-sm text-gray-600 mt-1">Всего приглашено</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <p className="text-3xl font-bold text-green-600">{stats.cards_issued}</p>
                  <p className="text-sm text-gray-600 mt-1">Карт оформлено</p>
                </div>
              </div>
              <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
                <p className="text-sm text-gray-700">
                  <Icon name="TrendingUp" size={16} className="inline mr-1" />
                  Потенциальный доход: <strong>{stats.total_referrals * 200}₽</strong>
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Заработано: <strong>{stats.cards_issued * 200}₽</strong>
                </p>
              </div>
            </Card>

            <Card className="bg-white p-6 shadow-xl">
              <h3 className="font-bold text-lg mb-3">Как это работает?</h3>
              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="bg-alfa-red text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">1</div>
                  <div>
                    <p className="font-semibold">Поделитесь промокодом</p>
                    <p className="text-sm text-gray-600">Отправьте друзьям в Telegram</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="bg-alfa-red text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">2</div>
                  <div>
                    <p className="font-semibold">Друг оформляет карту</p>
                    <p className="text-sm text-gray-600">По вашему промокоду</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="bg-alfa-red text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">3</div>
                  <div>
                    <p className="font-semibold">Получаете вознаграждение</p>
                    <p className="text-sm text-gray-600">200₽ на ваш баланс</p>
                  </div>
                </div>
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <Card className="bg-white p-6 shadow-xl">
              <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                <Icon name="Receipt" size={20} className="text-alfa-red" />
                История операций
              </h3>
              {transactions.length === 0 ? (
                <div className="text-center py-8">
                  <Icon name="Inbox" size={48} className="mx-auto text-gray-300 mb-3" />
                  <p className="text-gray-500">Пока нет операций</p>
                  <p className="text-sm text-gray-400 mt-1">Приглашайте друзей для получения вознаграждений</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {transactions.map((tx) => (
                    <div key={tx.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="bg-green-100 p-2 rounded-full">
                          <Icon name="Plus" size={16} className="text-green-600" />
                        </div>
                        <div>
                          <p className="font-semibold text-sm">{tx.description}</p>
                          <p className="text-xs text-gray-500">{new Date(tx.created_at).toLocaleDateString('ru-RU')}</p>
                        </div>
                      </div>
                      <p className="font-bold text-green-600">+{tx.amount}₽</p>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
