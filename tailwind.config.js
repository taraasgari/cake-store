module.exports = {
  content: [
    './first/templates/**/*.html',
    './customer_care/templates/**/*.html',
    './first/**/*.py',
    './customer_care/**/*.py',
    './static/js/**/*.js',
  ],
  safelist: [
    'from-yellow-400',
    'to-orange-500',
    'from-red-500',
    'to-pink-600'
  ],
  theme: { extend: {} },
  plugins: []
};
