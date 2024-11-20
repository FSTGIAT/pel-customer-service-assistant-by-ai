module.exports = {
    moduleFileExtensions: ['js', 'jsx', 'json', 'vue'],
    transform: {
      '^.+\\.vue$': '@vue/vue3-jest',
      '^.+\\.(js|jsx)?$': 'babel-jest'
    },
    moduleNameMapper: {
      '^@/(.*)$': '<rootDir>/src/$1'
    },
    testEnvironment: 'jsdom',
    testMatch: [
      '<rootDir>/test/**/*.test.js'
    ],
    testPathIgnorePatterns: ['/node_modules/'],
    collectCoverage: true,
    collectCoverageFrom: [
      'src/**/*.{js,vue}',
      '!src/main.js',
      '!**/node_modules/**'
    ]
  }